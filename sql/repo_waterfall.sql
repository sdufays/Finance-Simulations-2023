-- SET BOUNDARIES FOR PAYMENTDUEDATES VALUES
DECLARE @start DATE = '2023-06-30';
DECLARE @end DATE = '2024-06-30';

-- CREATE + OPEN NOTEDATA CTE THAT JOINS THE THREE TABLES BY LID
WITH NoteData AS (
    -- select relevant columns
    SELECT
        d.DealName,
        n.PID,
        n.NoteName,
        f.BusinessUnit,
        f.PariPassuSplit,
        f.FinancingSourceName,
        fb.PaymentDueDates,
        fb.InterestDueatCurrentRate,
        cf.InterestDueatCurrentRate * f.PariPassuSplit AS LoanInterestIncome
    FROM [ILAS].dbo.Note n 
    INNER JOIN [ILAS].dbo.Deal d 
        ON n.DealID = d.DealID -- join by deal id as specified in doc 
    INNER JOIN [ILAS].dbo.FinancingBUSetup f 
        ON n.LID = f.LID -- join by LID
    INNER JOIN [ILSCommon].dbo.FinancingCashflowBU fb 
        ON n.LID = fb.LID -- join by LID
        AND f.BusinessUnit = fb.BusinessUnit -- join by BusinessUnit
        AND fb.PaymentDueDates IS NOT NULL -- make sure payment due dates isn't null
        AND fb.ScenarioID = 2 -- filter for treasury team scenario
    INNER JOIN [ILSCommon].dbo.Cashflow cf 
        ON n.LID = cf.LID -- join by LID
        AND EOMONTH(fb.PaymentDueDates, 0) = EOMONTH(cf.PaymentDates, 0) -- join by end of month PaymentDueDates, aligning them, no offset 
        AND cf.ScenarioID = 2 -- filter for treasury team scenario & don't need to check for null payment date again ( i think )
    WHERE n.Status = 'Active' AND (fb.PaymentDueDates <= @end AND fb.PaymentDueDates >= @start)
),

-- CREATE + OPEN RANKEDDATA CTE, WHICH GETS NOTEDATA CTE TABLE AND ADDS ROWNUM COLUMN
RankedData AS (
    SELECT
        DealName,
        PID,
        NoteName,
        FinancingSourceName,
        PaymentDueDates,
        LoanInterestIncome,
        InterestDueatCurrentRate,
        ROW_NUMBER() OVER ( 
            PARTITION BY PID, FinancingSourceName
            ORDER BY PaymentDueDates
        ) AS RowNum
    FROM NoteData
)

-- OUTPUTS COMPLETED TABLE
SELECT
    DealName,
    PID,
    NoteName,
    FinancingSourceName,
    PaymentDueDates,
    LoanInterestIncome,
    InterestDueatCurrentRate,
    LoanInterestIncome - InterestDueatCurrentRate AS NetInterestMargin
FROM RankedData;


