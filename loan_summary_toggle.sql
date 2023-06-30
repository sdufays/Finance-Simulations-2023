--********** USER SETS MODE VARIABLE HERE ************--
DECLARE @mode varchar(50) = 'Funding' -- either Paydown or Funding


--------------------------------------
DECLARE @sql varchar(max)
SET @sql = '
    DECLARE @asofdate datetime = ''6-15-2023''
    DECLARE @end datetime = ''6-30-2024'';
    DECLARE @mode varchar(50) = ''' + @mode + ''';

    -- CREATE LOANDATA CTE JOINING LOAN AND TRANSACTIONENTRYARCHIVE TABLES
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
    -- CALCUALTE LOAN/REPO FUNDING AMOUNTS
    IF @mode = 'Funding'
    BEGIN
        SET @sql = @sql + '
            CASE WHEN t.TransactionType = ''Loan Future Funding'' THEN -1 * t.Amount ELSE 0 END AS Loan' + @mode + 'Amount,
            CASE WHEN t.TransactionType IN (''Loan Financing Draw'', ''CMBS Financing Draw'') THEN t.Amount ELSE 0 END AS Repo' + @mode + 'Amount, '
    END
    -- CALCULATE LOAN/REPO PAYDOWN AMOUNTS
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
    
    -- ONLY SHOW FUNDING TRANSACTIONS IN FUNDING TABLE
    IF @mode = 'Funding'
    BEGIN
        SET @sql = @sql + 't.TransactionType IN (''Loan Future Funding'',''Loan Financing Draw'', ''CMBS Financing Draw'')'
    END
    -- ONLY SHOW PAYDOWN TRANSACTIONS IN PAYDOWN TABLE
    ELSE IF @mode = 'Paydown'
    BEGIN
        SET @sql = @sql + 't.TransactionType IN (''Loan Curtailment'', ''Loan Balloon Payment'', ''CMBS Curtailment'',''Loan Financing Curtailment'', ''CMBS Financing curtailment'')'
    END

    SET @sql = @sql + '
    
    )
    -- OUTPUT FINAL TABLE
    SELECT 
        FamilyDealName AS [DealName],
        TransDate AS [TransactionDate],
        LoanSubStauts3 AS [ConstructionTag],
        PropertyType,
        AuditDate,
        AssetStatus, 
        SUM(Loan' + @mode + 'Amount) AS TotalLoan' + @mode + 'Amount,
        SUM(Repo' + @mode + 'Amount) AS TotalRepo' + @mode + 'Amount,
        SUM(Loan' + @mode + 'Amount) - SUM(Repo' + @mode + 'Amount) AS Net' + @mode + ',
        LineName
    FROM LoanData
    GROUP BY FamilyDealName, TransDate, LoanSubStauts3, PropertyType, AuditDate, AssetStatus, LineName
    ORDER BY TransDate'

-- EXECUTE DYNAMIC SQL
EXEC(@sql);