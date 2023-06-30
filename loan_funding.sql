use bsm
go

DECLARE @asofdate datetime = '6-15-2023'
DECLARE @end datetime = '6-30-2024';

--SELECT * FROM [BSM].dbo.Loan WHERE LoanStatus = 'Active' 
--and LoanSubStauts3 = 'Pre-development'

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
            WHEN t.TransactionType = 'Loan Financing Draw' or t.TransactionType = 'CMBS Financing Draw' THEN t.Amount
            ELSE 0
        END AS RepoFinancingDrawAmount,
        t.LineName
    -- from the joined two tables (join on PID/LoanID)
    FROM [BSM].dbo.Loan l
        INNER JOIN [BSM].dbo.TransactionEntryArchive t
        ON l.LoanID = t.PeopleSoftID
    -- loan must be active
    WHERE l.LoanStatus = 'Active' 
        -- audit date must be as of
        AND t.AuditDate = @asofdate 
        -- asset must be lending
        AND t.AssetStatus = 'Lending'
        -- transaction date must be between start and end
        AND t.TransDate >= @asofdate AND t.TransDate <= @end
)



SELECT 
    sub.DealName,
    sub.TransactionDate,
    ld.LoanSubStauts3 AS [ConstructionTag],
    ld.PropertyType, 
    ld.AuditDate,
    ld.AssetStatus,
    ld.LoanFundingAmount,
    ld.RepoFinancingDrawAmount,
    ld.LoanFundingAmount - ld.RepoFinancingDrawAmount AS NetFunding,
    ld.LineName
FROM (
    SELECT 
        FamilyDealName AS [DealName], 
        TransDate AS [TransactionDate], 
        SUM(LoanFundingAmount) AS TotalLoanFundingAmount,
        SUM(RepoFinancingDrawAmount) AS TotalRepoFinancingDrawAmount
    FROM LoanData
    GROUP BY FamilyDealName, TransDate
) sub
INNER JOIN LoanData ld
ON sub.DealName = ld.FamilyDealName AND sub.TransactionDate = ld.TransDate 
    AND sub.TotalLoanFundingAmount = ld.LoanFundingAmount 
    AND sub.TotalRepoFinancingDrawAmount = ld.RepoFinancingDrawAmount;