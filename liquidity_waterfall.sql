-- SET BOUNDARIES FOR ACTUALPAYMENTDATE VALUES
DECLARE @start DATE = '2023-06-30';
DECLARE @end DATE = '2024-06-30';

-- CREATE + OPEN LOANDATA CTE THAT JOINS THE THREE TABLES BY LOAN ID
WITH LoanData AS (
    -- select relevant columns
    SELECT 
        l.FamilyDealName, 
        l.LoanID, 
        l.LoanName, 
        p.RepoLineNameforthePeriod, 
        p.ActualPaymentDate, 
        p.FinancingInterestExpense,
        cf.CFNetInterest,
        cf.CFMonth
    -- from the joined three tables
    FROM [BSM].dbo.Loan l -- defining loan table as l 
    INNER JOIN [BSM].dbo.FinancingPaymentData p -- defining the finance payment data as p 
        ON l.LoanID = p.LoanID -- join by loan id
        AND p.RepoLineNameforthePeriod IS NOT NULL -- make sure repo line name isn't null, why is this neccessary 
    INNER JOIN [BSM].dbo.Cashflow cf -- define cashflow as cf 
        ON l.LoanID = cf.LoanID -- join by loan id
        AND cf.CFMonth = p.Month -- make sure months are the same in cashflow and financing payment
    -- where loan is active and payment date is within the boundaries
    WHERE l.LoanStatus = 'Active' AND (p.ActualPaymentDate <= @end AND p.ActualPaymentDate >= @start)
),

-- CREATE + OPEN RANKEDDATA CTE, WHICH GETS LOANDATA CTE TABLE AND ADDS ROWNUM COLUMN
-- rownum column generates unique row number for each row
RankedData AS (
    SELECT 
        FamilyDealName, 
        LoanID, 
        LoanName, 
        RepoLineNameforthePeriod, 
        ActualPaymentDate, 
        FinancingInterestExpense, 
        CFNetInterest, 
        CFMonth,
        ROW_NUMBER() OVER ( -- OVER partitions both loanID and repolinename, then orders by the month/paymentdate
            PARTITION BY LoanID, RepoLineNameforthePeriod 
            ORDER BY CFMonth, ActualPaymentDate
        ) AS RowNum
    FROM LoanData
)

-- OUTPUTS COMPLETED TABLE
SELECT 
    FamilyDealName, 
    LoanID, 
    LoanName, 
    RepoLineNameforthePeriod, 
    ActualPaymentDate, 
    FinancingInterestExpense, 
    CFNetInterest, 
    CFMonth,
    -- calculates net interest margin value
    CFNetInterest - FinancingInterestExpense AS NetInterestMargin
FROM RankedData;