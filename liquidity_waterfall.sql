DECLARE @start DATE = '2023-06-30';
DECLARE @end DATE = '2024-06-30';

 

WITH LoanData AS (
    SELECT 
        l.FamilyDealName, 
        l.LoanID, 
        l.LoanName, 
        p.RepoLineNameforthePeriod, 
        p.ActualPaymentDate, 
        p.FinancingInterestExpense,
        cf.CFNetInterest,
        cf.CFMonth
    FROM [BSM].dbo.Loan l
    INNER JOIN [BSM].dbo.FinancingPaymentData p
        ON l.LoanID = p.LoanID
        AND p.RepoLineNameforthePeriod IS NOT NULL
    INNER JOIN [BSM].dbo.Cashflow cf
        ON l.LoanID = cf.LoanID
        AND cf.CFMonth = p.Month
    WHERE l.LoanStatus = 'Active'
),
 

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
        ROW_NUMBER() OVER (
            PARTITION BY LoanID, RepoLineNameforthePeriod 
            ORDER BY CFMonth, ActualPaymentDate
        ) AS RowNum
    FROM LoanData
)

 

SELECT 
    FamilyDealName, 
    LoanID, 
    LoanName, 
    RepoLineNameforthePeriod, 
    ActualPaymentDate, 
    FinancingInterestExpense, 
    CFNetInterest, 
    CFMonth,
    CFNetInterest - FinancingInterestExpense AS NetInterestMargin,
    DATEADD(DAY, RowNum - 1, @start) AS PaymentDate
FROM RankedData
WHERE DATEADD(DAY, RowNum - 1, @start) <= @end;