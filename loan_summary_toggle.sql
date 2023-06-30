-- https://www.sqlshack.com/dynamic-sql-in-sql-server/

--select * from [BSM].dbo.TransactionEntryArchive 
--where TransactionType IN('Loan Curtailment', 'Loan Balloon Payment', 'CMBS Curtailment','Loan Financing Curtailment', 'CMBS Financing Curtailment')
--AND TransDate >='6-15-2023' AND TransDate <='6-30-2024'
--AND AuditDate = '6-15-2023'
--AND AssetStatus = 'Lending'
--ORDER BY TransDate

DECLARE @sql varchar(max)
DECLARE @mode varchar(50) = 'Paydown' -- either paydown or funding
SET @sql = '

 

    DECLARE @asofdate datetime = ''6-15-2023''
    DECLARE @end datetime = ''6-30-2024'';
    DECLARE @mode varchar(50) = ''' + @mode + '''; -- either paydown or funding

 

    WITH LoanData AS (
        SELECT 
            l.LoanID,
            l.FamilyDealName, 
            l.LoanSubStauts3, 
            l.PropertyType, 
            t.AuditDate,
            t.AssetStatus,
            t.TransDate, 
            t.TransactionType,'

 

    IF @mode = 'Funding'
    BEGIN
        SET @sql = @sql + '
            CASE WHEN t.TransactionType = ''Loan Future Funding'' THEN -1 * t.Amount ELSE 0 END AS Loan' + @mode + 'Amount,
            CASE WHEN t.TransactionType IN (''Loan Financing Draw'', ''CMBS Financing Draw'') THEN t.Amount ELSE 0 END AS Repo' + @mode + 'Amount, '
    END
    ELSE IF @mode = 'Paydown'
    BEGIN
        SET @sql = @sql + '
            CASE WHEN t.TransactionType IN(''Loan Curtailment'', ''Loan Balloon Payment'', ''CMBS Curtailment'') THEN t.Amount ELSE 0 END AS Loan' + @mode + 'Amount,
            CASE WHEN t.TransactionType IN (''Loan Financing Curtailment'', ''CMBS Financing curtailment'') THEN t.Amount ELSE 0 END AS Repo' + @mode + 'Amount, '
    END

 

    SET @sql = @sql + '
            t.LineName
        FROM [BSM].dbo.Loan l
            INNER JOIN [BSM].dbo.TransactionEntryArchive t ON l.LoanID = t.PeopleSoftID
        WHERE l.LoanStatus = ''Active'' 
            AND t.AuditDate = @asofdate
            AND t.AssetStatus = ''Lending'' 
            AND t.TransDate >= @asofdate AND t.TransDate <= @end
            AND ' 
    
    IF @mode = 'Funding'
    BEGIN
        SET @sql = @sql + 't.TransactionType IN (''Loan Future Funding'',''Loan Financing Draw'', ''CMBS Financing Draw'')'
    END
    ELSE IF @mode = 'Paydown'
    BEGIN
        SET @sql = @sql + 't.TransactionType IN (''Loan Curtailment'', ''Loan Balloon Payment'', ''CMBS Curtailment'',''Loan Financing Curtailment'', ''CMBS Financing curtailment'')'
    END

    SET @sql = @sql + '
    
    )

 

    SELECT 
        sub.DealName,
        sub.TransactionDate,
        ld.LoanSubStauts3 AS [ConstructionTag],
        ld.PropertyType, 
        ld.AuditDate,
        ld.AssetStatus,
        ld.Loan' + @mode + 'Amount,
        ld.Repo' + @mode + 'Amount,
        ld.Loan' + @mode + 'Amount - ld.Repo' + @mode + 'Amount AS [Net' + @mode + '],
        ld.LineName,
        ld.TransactionType
    FROM (
        SELECT 
            FamilyDealName AS [DealName], 
            TransDate AS [TransactionDate], 
            SUM(Loan' + @mode + 'Amount) AS TotalLoan' + @mode + 'Amount,
            SUM(Repo' + @mode + 'Amount) AS TotalRepo' + @mode + 'Amount
        FROM LoanData
        GROUP BY FamilyDealName, TransDate
    ) sub
    INNER JOIN LoanData ld ON sub.DealName = ld.FamilyDealName AND sub.TransactionDate = ld.TransDate 
        AND sub.TotalLoan' + @mode + 'Amount = ld.Loan' + @mode + 'Amount 
        AND sub.TotalRepo' + @mode + 'Amount = ld.Repo' + @mode + 'Amount;'
 

-- Execute the dynamic SQL statement
EXEC(@sql);