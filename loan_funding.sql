DECLARE @asofdate datetime = '6-15-2023'
DECLARE @end datetime = '6-30-2024';

--SELECT LoanSubStauts3 FROM [BSM].dbo.Loan l WHERE l.LoanStatus = 'Active' 

-- create CTE
WITH LoanData AS (
    -- select relevant columns from joined table
    SELECT 
        l.LoanID,
        l.FamilyDealName, 
        l.LoanSubStauts3, 
        l.PropertyType, 
        t.AuditDate,
        t.AssetStatus,
        t.TransDate, 
        CASE 
            WHEN t.TransactionType = 'Loan Future Funding' THEN -1 * t.Amount
            ELSE 0
        END AS LoanFundingAmount,
        CASE 
            WHEN t.TransactionType = 'Loan Financing Draw' THEN t.Amount
            ELSE 0
        END AS RepoFinancingDrawAmount,
        t.LineName
    -- from the joined two tables (join on PID/LoanID)
    FROM [BSM].dbo.Loan l
        INNER JOIN [BSM].dbo.TransactionEntryArchive t
        ON l.LoanID = t.PeopleSoftID
    -- loan must be active
    WHERE l.LoanStatus = 'Active' 
        -- only include transactions of these types
        AND t.TransactionType IN ('Loan Future Funding', 'Loan Financing Draw')
        -- audit date must be as of
        AND t.AuditDate = @asofdate 
        -- asset must be lending
        AND t.AssetStatus = 'Lending'
        -- transaction date must be between start and end
        AND t.TransDate >= @asofdate AND t.TransDate <= @end
)

SELECT 
    FamilyDealName AS [DealName], 
    TransDate AS [TransactionDate], 
    LoanID, 
    LoanSubStauts3 AS [ConstructionTag],
    PropertyType, 
    AuditDate,
    AssetStatus,
    SUM(LoanFundingAmount) AS LoanFundingAmount,
    SUM(RepoFinancingDrawAmount) AS RepoFinancingDrawAmount,
    SUM(LoanFundingAmount - RepoFinancingDrawAmount) AS NetFunding,
    LineName
FROM LoanData
GROUP BY FamilyDealName, TransDate, LoanID, LoanSubStauts3, PropertyType, AuditDate, AssetStatus, LineName;