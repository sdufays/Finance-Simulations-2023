use bsm

go

 

DECLARE @asofdate datetime = '6-15-2023'

DECLARE @end datetime = '6-30-2024';

 

--SELECT DISTINCT TransactionType FROM [BSM].dbo.TransactionEntryArchive;

--select * from [BSM].dbo.TransactionEntryArchive 

--where TransactionType IN('Loan Curtailment', 'Loan Balloon Payment','Loan Financing Curtailment')

--AND TransDate >='6-15-2023' AND TransDate <='6-30-2024'

--AND AuditDate = '6-15-2023'

--AND AssetStatus = 'Lending'

--ORDER BY TransDate

 

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

        CASE WHEN 

            t.TransactionType IN('Loan Curtailment', 'Loan Balloon Payment', 'CMBS Curtailment') 

            THEN t.Amount 

            ELSE 0 

        END AS LoanPaydownAmount,

        CASE WHEN 

            t.TransactionType IN ('Loan Financing Curtailment', 'CMBS Financing curtailment') 

            THEN t.Amount 

            ELSE 0 

        END AS RepoPaydownAmount, 

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

        AND t.TransactionType IN( 'Loan Financing Curtailment', 'CMBS Financing curtailment',  'CMBS Fin Curtailment','Loan Curtailment', 'Loan Balloon Payment', 'CMBS Curtailment' )

)

--select FamilyDealName, Transdate, LoanID, LoanPaydownAmount 

--from LoanData 

--order by FamilyDealName, Transdate

 

--select FamilyDealName, Transdate 

--from LoanData

--group by FamilyDealName, TransDate 

--order by TransDate

 

 

SELECT 

    sub.DealName,

    sub.TransactionDate,

    ld.LoanSubStauts3 AS [ConstructionTag],

    ld.PropertyType, 

    ld.AuditDate,

    ld.AssetStatus,

    ld.LoanPaydownAmount,

    ld.RepoPaydownAmount,

    ld.LoanPaydownAmount - ld.RepoPaydownAmount AS NetPaydown,

    ld.LineName

FROM (

    SELECT 

        FamilyDealName AS [DealName], 

        TransDate AS [TransactionDate], 

        SUM(LoanPaydownAmount) AS TotalLoanPaydownAmount,

        SUM(RepoPaydownAmount) AS TotalRepoPaydownAmount

    FROM LoanData

    GROUP BY FamilyDealName, TransDate

) sub

INNER JOIN LoanData ld

ON sub.DealName = ld.FamilyDealName AND sub.TransactionDate = ld.TransDate 

    --AND sub.TotalLoanPaydownAmount = ld.LoanPaydownAmount 

    --AND sub.TotalRepoPaydownAmount = ld.RepoPaydownAmount;
use bsm
go

DECLARE @asofdate datetime = '6-15-2023'
DECLARE @end datetime = '6-30-2024';

--SELECT DISTINCT TransactionType FROM [BSM].dbo.TransactionEntryArchive;
--select * from [BSM].dbo.TransactionEntryArchive 
--where TransactionType IN('Loan Curtailment', 'Loan Balloon Payment','Loan Financing Curtailment')
--AND TransDate >='6-15-2023' AND TransDate <='6-30-2024'
--AND AuditDate = '6-15-2023'
--AND AssetStatus = 'Lending'
--ORDER BY TransDate

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
        CASE WHEN 
            t.TransactionType IN('Loan Curtailment', 'Loan Balloon Payment', 'CMBS Curtailment') 
            THEN t.Amount 
            ELSE 0 
        END AS LoanPaydownAmount,
        CASE WHEN 
            t.TransactionType IN ('Loan Financing Curtailment', 'CMBS Financing curtailment') 
            THEN t.Amount 
            ELSE 0 
        END AS RepoPaydownAmount, 
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
        AND t.TransactionType IN( 'Loan Financing Curtailment', 'CMBS Financing curtailment',  'CMBS Fin Curtailment','Loan Curtailment', 'Loan Balloon Payment', 'CMBS Curtailment' )
)
--select FamilyDealName, Transdate, LoanID, LoanPaydownAmount 
--from LoanData 
--order by FamilyDealName, Transdate

--select FamilyDealName, Transdate 
--from LoanData
--group by FamilyDealName, TransDate 
--order by TransDate



SELECT 
    sub.DealName,
    sub.TransactionDate,
    ld.LoanSubStauts3 AS [ConstructionTag],
    ld.PropertyType, 
    ld.AuditDate,
    ld.AssetStatus,
    ld.LoanPaydownAmount,
    ld.RepoPaydownAmount,
    ld.LoanPaydownAmount - ld.RepoPaydownAmount AS NetPaydown,
    ld.LineName
FROM (
    SELECT 
        FamilyDealName AS [DealName], 
        TransDate AS [TransactionDate], 
        SUM(LoanPaydownAmount) AS TotalLoanPaydownAmount,
        SUM(RepoPaydownAmount) AS TotalRepoPaydownAmount
    FROM LoanData
    GROUP BY FamilyDealName, TransDate
) sub
INNER JOIN LoanData ld
ON sub.DealName = ld.FamilyDealName AND sub.TransactionDate = ld.TransDate 
    --AND sub.TotalLoanPaydownAmount = ld.LoanPaydownAmount 
    --AND sub.TotalRepoPaydownAmount = ld.RepoPaydownAmount;
