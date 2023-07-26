declare @pend as datetime = '3-31-2024' 
declare @sdate as datetime = '6-15-2023'
declare @auditdate as datetime = '6-15-2023'
declare @moend as datetime = EoMonth(@sdate)
declare @mostart as datetime
declare @lm_balance decimal(28, 15), @ff_delta decimal(28, 15), @pdwn_delta decimal(28, 15)
declare @repodraw_delta decimal(28, 15), @repopdwn_delta decimal(28, 15), @total_delta decimal(28, 15)
DECLARE @threshold DECIMAL(18, 2) = 5000000

declare @Body NVARCHAR(MAX),
@LiquiditySummaryTableBody NVARCHAR(MAX),
@LiquiditySummaryTableHead VARCHAR(1000),
@LiquiditySummaryTableTail VARCHAR(1000),
@CRELoanFFTableBody NVARCHAR(MAX),
@CRELoanFFTableHead VARCHAR(1000),
@CRELoanFFTableTail VARCHAR(1000),
@CRELoanPdwnTableBody NVARCHAR(MAX),
@CRELoanPdwnTableHead VARCHAR(1000),
@CRELoanPdwnTableTail VARCHAR(1000),
@CRERepoDrawTableBody NVARCHAR(MAX),
@CRERepoDrawTableHead VARCHAR(1000),
@CRERepoDrawTableTail VARCHAR(1000),
@CRERepoPdwnTableBody NVARCHAR(MAX),
@CRERepoPdwnTableHead VARCHAR(1000),
@CRERepoPdwnTableTail VARCHAR(1000)

IF OBJECT_ID('tempdb..#LiquiditySummary') IS NOT NULL
    DROP TABLE #LiquiditySummary
CREATE TABLE #LiquiditySummary(PeriodEndDate datetime, MoEndBalance decimal(28, 15), Lending_FFChange decimal(28, 15),
                            Lending_LoanPdwnChange decimal(28, 15), Lending_RepoDrawChange decimal(28, 15), 
							Lending_RepoPdwnChange decimal(28, 15), 
                            Updated_MoEndBalance decimal(28, 15)
                            )

WHILE @moend <= EoMonth(@pend, 0)
BEGIN
    set @mostart = (select 
                        case when @moend = EoMonth(@sdate, 0) 
                            then @sdate 
                        else EoMonth(@moend, -1) 
                    end);

    -- month end balance from most recent liquidity report:
    set @lm_balance = (select Amount 
                       from [BSM].dbo.TransactionEntryArchive ta
                       where AuditDate = @auditdate 
                           and TransactionType = 'Month End Cash + AUD Low Point'
                           and TransDate = @moend);

    WITH LiquidityChanges AS 
    (
        SELECT 
            archive_data.TransactionType AS TransactionType, 
            SUM(current_data.TrAmt - archive_data.TrAmt) AS Delta
        FROM
            (
            SELECT 
                FamilyDealName,
                SUM(Amount) AS TrAmt, 
                ta.TransactionType
            FROM [BSM].dbo.TransactionEntryArchive ta
            INNER JOIN [BSM].dbo.Loan l ON l.LoanID = ta.PeopleSoftID
            WHERE AuditDate = @auditdate 
                AND AssetStatus = 'Lending' 
                AND TransDate > @mostart AND TransDate <= @moend
                AND ta.TransactionType IN ('Loan Future Funding', 'Loan Curtailment', 'Loan Balloon Payment', 'CMBS Curtailment',
                                       'Loan Financing Draw', 'CMBS Financing Draw', 'Loan Financing Curtailment', 'CMBS Financing curtailment')
            GROUP BY FamilyDealName, ta.TransactionType
            ) archive_data
        LEFT JOIN
            (
            SELECT 
                FamilyDealName, 
                SUM(Amount) as TrAmt, 
                ta.TransactionType
            FROM [BSM].dbo.TransactionEntry ta
            INNER JOIN [BSM].dbo.Loan l ON l.LoanID = ta.PeopleSoftID
            WHERE TransDate > @mostart 
                AND TransDate <= @moend
                AND ta.TransactionType IN ('Loan Future Funding', 'Loan Curtailment', 'Loan Balloon Payment', 'CMBS Curtailment',
                                       'Loan Financing Draw', 'CMBS Financing Draw', 'Loan Financing Curtailment', 'CMBS Financing curtailment')
            GROUP BY FamilyDealName, ta.TransactionType
            ) current_data ON archive_data.FamilyDealName = current_data.FamilyDealName AND archive_data.TransactionType = current_data.TransactionType
        GROUP BY archive_data.TransactionType
    )

    SELECT 
        -- change from loan ff projections
        @ff_delta = ISNULL(MAX(CASE WHEN TransactionType = 'Loan Future Funding' THEN Delta END), 0),
        -- change from loan pdwn projections
        @pdwn_delta = ISNULL(MAX(CASE WHEN TransactionType IN ('Loan Curtailment', 'Loan Balloon Payment', 'CMBS Curtailment') THEN Delta END), 0),
        -- change from repo draw projections
        @repodraw_delta = ISNULL(MAX(CASE WHEN TransactionType IN ('Loan Financing Draw', 'CMBS Financing Draw') THEN Delta END), 0),
        -- change from repo pdwn projections
        @repopdwn_delta = ISNULL(MAX(CASE WHEN TransactionType IN ('Loan Financing Curtailment', 'CMBS Financing curtailment') THEN Delta END), 0)
    FROM LiquidityChanges;

    set @total_delta = isnull(@total_delta, 0) + @ff_delta + @pdwn_delta + isnull(@repodraw_delta, 0) - isnull(@repopdwn_delta, 0);

    INSERT INTO #LiquiditySummary(PeriodEndDate, MoEndBalance, Lending_FFChange, Lending_LoanPdwnChange, 
                            Lending_RepoDrawChange, Lending_RepoPdwnChange, 
                            Updated_MoEndBalance
                            )
    VALUES(@moend, @lm_balance, @ff_delta, @pdwn_delta, 
            @repodraw_delta, -@repopdwn_delta, 
            @lm_balance + @total_delta);

    set @moend = EOMONTH(@moend, 1);
END


SET @Body = '<html><head>Projected liquidity month end cash + approved undrawn balance using most recent liquidity report as of ' 
    + CAST(FORMAT(@auditdate, 'd', 'us') as nvarchar) 
    + ' as a starting point and adding changing in cash flows projections from Lending Segment<br>' 
    + '<style>'
    + 'table {border-collapse: collapse; width: 90%; margin: auto;}'
    + 'td, th {border: 1px solid black; padding: 8px; text-align: center; font-size: 12px; width: 50px;}'
    + 'th {background-color: #000080; color: #D3D3D3; padding-top: 15px; padding-bottom: 15px;}'
    + 'b {font-size: 16px; display: block; text-align: center; color: #000080; margin: 20px 0px;}'
    + '</style>' + '</head>' + '<body>'


SET @LiquiditySummaryTableHead = ''
    + '<br><table>'
    + '<tr>'
    + '<th>Month End</th>'
    + '<th>Mo End Cash + AUD Balance from Liquidity Report</th>'
    + '<th>Lending - Change in Loan Funding projections</th>'
    + '<th>Lending - Change in Loan Pdwn projections</th>'
    + '<th>Lending - Change in Repo Draw projections</th>'
    + '<th>Lending - Change in Repo Pdwn projections</th>'
    + '<th>Projected Mo End Cash + AUD Balance</th>'
    + '<th>Cumulative Liquidity Impact from changes in projections for Lending segment</th>'
    + '</tr>'


	SET @LiquiditySummaryTableBody = (select td = FORMAT(PeriodEndDate, 'd', 'us'), 
                                td = FORMAT(MoEndBalance, '#,###'), 
                                td = FORMAT(Lending_FFChange, '#,###'), 
                                td = FORMAT(Lending_LoanPdwnChange, '#,###'),
                                td = FORMAT(Lending_RepoDrawChange, '#,###'), 
                                td = FORMAT(Lending_RepoPdwnChange, '#,###'), 
                                td = FORMAT(Updated_MoEndBalance, '#,###'),
                                td = FORMAT(Updated_MoEndBalance - MoEndBalance, '#,###')
                        from #LiquiditySummary

					 FOR   XML RAW('tr'),
					  ELEMENTS

					)
	SET @LiquiditySummaryTableTail = '</table><br><br>' ;
    SELECT  @LiquiditySummaryTableBody = @LiquiditySummaryTableHead + ISNULL(@LiquiditySummaryTableBody, '') + @LiquiditySummaryTableTail
	
     --- Table showing top 10 CRE loans with Pdwn changes:
    SET @CRELoanPdwnTableHead = ''
    + ' <br><b>Top 3 most influential CRE loans per month when change in loan paydown liquidity is greather than 5 million</b>'
    + '<table>'
    + '<tr>'
    + '<th>Transaction Date</th>'
    + '<th>Deal Name</th>'
    + '<th>Most recent liquidity report</th>'
    + '<th>Current data set</th>'
    + '<th>Liquidity Impact</th>'
    + '</tr>';


    WITH LoanPdwnDeltas AS (
          SELECT 
            PeriodEndDate,
            MONTH(PeriodEndDate) AS [CurrentMonth],
            Lending_LoanPdwnChange
          FROM #LiquiditySummary
          WHERE ABS(Lending_LoanPdwnChange) > @threshold
        )

    SELECT @CRELoanPdwnTableBody = (
        SELECT 
    		td = FORMAT(joined.TransDate,'d','us'),
            --td = joined.CurrentMonth,
    		td = joined.FamilyDealName, 
            td = ISNULL(CONVERT(NVARCHAR, FORMAT(joined.lrTrAmt, 'N0')), '0'), 
            td = ISNULL(CONVERT(NVARCHAR, FORMAT(joined.crTrAmt, 'N0')), '0'),
            td = ISNULL(CONVERT(NVARCHAR, FORMAT((joined.crTrAmt - joined.lrTrAmt), 'N0')), '0')
    	FROM
    	(
            SELECT 
                MAX(COALESCE(cr.ExactDate, lr.ExactDate)) AS TransDate,
                MONTH(COALESCE(lr.TransDate, cr.TransDate)) AS [CurrentMonth],
                COALESCE(lr.FamilyDealName, cr.FamilyDealName) AS FamilyDealName, 
                SUM(COALESCE(lr.TrAmt, 0)) AS 'lrTrAmt',
                SUM(COALESCE(cr.TrAmt, 0)) AS 'crTrAmt',
                SUM(COALESCE(cr.TrAmt, 0)) - SUM(COALESCE(lr.TrAmt, 0)) AS Delta
            FROM
            (SELECT 
                    FamilyDealName, 
                    SUM(Amount) AS 'TrAmt',
                    DATEADD(month, DATEDIFF(month, 0, TransDate), 0) AS TransDate,
                    MAX(TransDate) AS ExactDate
                FROM [BSM].dbo.TransactionEntryArchive ta
                INNER JOIN [BSM].dbo.Loan l ON l.LoanID = ta.PeopleSoftID
                WHERE 
                    AuditDate = @auditdate AND 
                    AssetStatus = 'Lending' AND 
                    TransDate >= @sdate AND 
                    TransDate <= @pend AND 
                    (ta.TransactionType = 'Loan Curtailment' OR ta.TransactionType = 'Loan Balloon Payment' OR ta.TransactionType = 'CMBS Curtailment')
                GROUP BY FamilyDealName, DATEADD(month, DATEDIFF(month, 0, TransDate), 0)
            ) lr
            FULL OUTER JOIN
            (SELECT 
                    FamilyDealName, 
                    SUM(Amount) AS 'TrAmt',
                    DATEADD(month, DATEDIFF(month, 0, TransDate), 0) AS TransDate,
                    MAX(TransDate) AS ExactDate
                FROM [BSM].dbo.TransactionEntry ta
                INNER JOIN [BSM].dbo.Loan l ON l.LoanID = ta.PeopleSoftID
                WHERE 
                    TransDate >= @sdate AND 
                    TransDate <= @pend AND 
                    (ta.TransactionType = 'Loan Curtailment' OR ta.TransactionType = 'Loan Balloon Payment' OR ta.TransactionType = 'CMBS Curtailment')
                GROUP BY FamilyDealName, DATEADD(month, DATEDIFF(month, 0, TransDate), 0)
            ) cr ON lr.FamilyDealName = cr.FamilyDealName AND lr.TransDate = cr.TransDate
            GROUP BY MONTH(COALESCE(lr.TransDate, cr.TransDate)),
                COALESCE(lr.FamilyDealName, cr.FamilyDealName)
    	) AS joined
    	INNER JOIN LoanPdwnDeltas LPD ON LPD.CurrentMonth = joined.CurrentMonth
        WHERE ABS(joined.Delta) >= 5000000
    	ORDER BY joined.TransDate
	    FOR XML RAW('tr'), ELEMENTS
    )

	SET @CRELoanPdwnTableTail = '</table><br><br>' ;
    SELECT  @CRELoanPdwnTableBody = @CRELoanPdwnTableHead + ISNULL(@CRELoanPdwnTableBody, '') + @CRELoanPdwnTableTail

    --- Table showing top 10 CRE loans with FF funding changes:
    SET @CRELoanFFTableHead = ''
    + ' <br><b>Top 3 most influential CRE loans per month when change in future funding liquidity is greather than 5 million</b>'
    + '<table>'
    + '<tr>'
    + '<th>Transaction Date</th>'
    + '<th>Deal Name</th>'
    + '<th>Most recent liquidity report</th>'
    + '<th>Current data set</th>'
    + '<th>Liquidity Impact</th>'
    + '</tr>';

    
    WITH FFDeltas AS (
        SELECT 
        PeriodEndDate,
        MONTH(PeriodEndDate) AS [CurrentMonth],
        Lending_FFChange
        FROM #LiquiditySummary
        WHERE ABS(Lending_FFChange) > @threshold
    )

	SELECT @CRELoanFFTableBody = (
    SELECT 
    		td = FORMAT(joined.TransDate,'d','us'),
    		td = joined.FamilyDealName, 
    		td = FORMAT(joined.lrTrAmt, '#,###'), 
    		td = FORMAT(joined.crTrAmt, '#,###'),
    		td = FORMAT(joined.crTrAmt - joined.lrTrAmt, '#,###')
    	FROM
    	(
    		SELECT 
    			MONTH(lr.TransDate) AS [CurrentMonth],
    			lr.FamilyDealName, 
    			lr.TrAmt AS 'lrTrAmt',
    			cr.TrAmt AS 'crTrAmt',
    			lr.TransDate--,
                --ROW_NUMBER() OVER (PARTITION BY MONTH(lr.TransDate) ORDER BY lr.TransDate DESC) AS RowNum
    		FROM
    		(
    			SELECT 
    				FamilyDealName, 
    				SUM(Amount) AS 'TrAmt',
    				TransDate
    			FROM [BSM].dbo.TransactionEntryArchive ta
    			INNER JOIN [BSM].dbo.Loan l ON l.LoanID = ta.PeopleSoftID
    			WHERE 
    				AuditDate = @auditdate AND 
    				AssetStatus = 'Lending' AND 
    				TransDate >= @sdate AND 
    				TransDate <= @pend AND 
    				ta.TransactionType = 'Loan Future Funding'
    			GROUP BY FamilyDealName, TransDate
    		) lr
    		LEFT JOIN
    		(
    			SELECT 
    				FamilyDealName, 
    				SUM(Amount) AS 'TrAmt',
    				TransDate
    			FROM [BSM].dbo.TransactionEntry ta
    			INNER JOIN [BSM].dbo.Loan l ON l.LoanID = ta.PeopleSoftID
    			WHERE 
    				TransDate >= @sdate AND 
    				TransDate <= @pend AND 
    				ta.TransactionType = 'Loan Future Funding'
    			GROUP BY FamilyDealName, TransDate
    		) cr ON lr.familydealname = cr.familydealname AND lr.TransDate = cr.TransDate
    		WHERE 
    			cr.TrAmt - lr.TrAmt <> 0 
    	) AS joined
    	INNER JOIN FFDeltas FFD ON FFD.CurrentMonth = joined.CurrentMonth
        --WHERE joined.RowNum <= 3
    	ORDER BY joined.TransDate
	    FOR XML RAW('tr'), ELEMENTS
    )

					
	SET @CRELoanFFTableTail = '</table><br><br>' ;
    SELECT  @CRELoanFFTableBody = @CRELoanFFTableHead + ISNULL(@CRELoanFFTableBody, '') + @CRELoanFFTableTail

    --- Table showing top 10 CRE loans with Repo Pdwn changes:
    SET @CRERepoPdwnTableHead = ''
    + ' <br><b>Top 3 most influential CRE loans per month when change in repo paydown liquidity is greather than 5 million</b>'
    + '<table>'
    + '<tr>'
    + '<th>Transaction Date</th>'
    + '<th>Deal Name</th>'
    + '<th>Most recent liquidity report</th>'
    + '<th>Current data set</th>'
    + '<th>Liquidity Impact</th>'
    + '</tr>';

    WITH RepoPdwnDeltas AS (
        SELECT 
        PeriodEndDate,
        MONTH(PeriodEndDate) AS [CurrentMonth],
        Lending_RepoPdwnChange
        FROM #LiquiditySummary
        WHERE ABS(Lending_RepoPdwnChange) > @threshold
    )

	SELECT @CRERepoPdwnTableBody = (
        SELECT 
    		td = FORMAT(joined.TransDate,'d','us'),
    		td = joined.FamilyDealName, 
    		td = FORMAT(joined.lrTrAmt, '#,###'), 
    		td = FORMAT(joined.crTrAmt, '#,###'),
    		td = FORMAT(joined.crTrAmt - joined.lrTrAmt, '#,###')
    	FROM
    	(SELECT 
            MONTH(lr.TransDate) AS [CurrentMonth],
            isnull(lr.FamilyDealName, cr.FamilyDealName) AS FamilyDealName, 
            SUM(lr.TrAmt) AS 'lrTrAmt',
            SUM(cr.TrAmt) AS 'crTrAmt',
            lr.TransDate--,
            --ROW_NUMBER() OVER (PARTITION BY MONTH(lr.TransDate) ORDER BY lr.TransDate DESC) AS RowNum
        FROM
            (SELECT 
    	            FamilyDealName, 
    	            SUM(Amount) AS 'TrAmt',
    	            TransDate
                FROM [BSM].dbo.TransactionEntryArchive ta
                INNER JOIN [BSM].dbo.Loan l ON l.LoanID = ta.PeopleSoftID
                WHERE 
    	            AuditDate = @auditdate AND 
    	            AssetStatus = 'Lending' AND 
    	            TransDate >= @sdate AND 
    	            TransDate <= @pend AND 
                    (ta.TransactionType = 'Loan Financing Curtailment' or ta.TransactionType = 'CMBS Financing curtailment')
                GROUP BY FamilyDealName, TransDate
            ) lr
            FULL OUTER JOIN
            (SELECT 
    	            FamilyDealName, 
    	            SUM(Amount) AS 'TrAmt',
    	            TransDate
                FROM [BSM].dbo.TransactionEntry ta
                INNER JOIN [BSM].dbo.Loan l ON l.LoanID = ta.PeopleSoftID
                WHERE 
    	            TransDate >= @sdate AND 
    	            TransDate <= @pend AND 
                    (ta.TransactionType = 'Loan Financing Curtailment' or ta.TransactionType = 'CMBS Financing curtailment')
                GROUP BY FamilyDealName, TransDate
            ) cr ON lr.familydealname = cr.familydealname 
            WHERE cr.TrAmt - lr.TrAmt <> 0 
            GROUP BY MONTH(lr.TransDate),
                isnull(lr.FamilyDealName, cr.FamilyDealName),
                lr.TransDate
    	) AS joined
    	INNER JOIN RepoPdwnDeltas RPD ON RPD.CurrentMonth = joined.CurrentMonth
        --WHERE joined.RowNum <= 3
    	ORDER BY joined.TransDate
	    FOR XML RAW('tr'), ELEMENTS
    )
	SET @CRERepoPdwnTableTail = '</table><br><br>' ;
    SELECT  @CRERepoPdwnTableBody = @CRERepoPdwnTableHead + ISNULL(@CRERepoPdwnTableBody, '') + @CRERepoPdwnTableTail

    --- Table showing top 10 CRE loans with Repo Draw changes:
    SET @CRERepoDrawTableHead = ''
    + ' <br><b>Top 3 most influential CRE loans per month when change in repo draw liquidity is greather than 5 million</b>'
    + '<table>'
    + '<tr>'
    + '<th>Transaction Date</th>'
    + '<th>Deal Name</th>'
    + '<th>Most recent liquidity report</th>'
    + '<th>Current data set</th>'
    + '<th>Liquidity Impact</th>'
    + '</tr>';

    WITH RepoDrawDeltas AS (
        SELECT 
        PeriodEndDate,
        MONTH(PeriodEndDate) AS [CurrentMonth],
        Lending_RepoDrawChange
        FROM #LiquiditySummary
        WHERE ABS(Lending_RepoDrawChange) > @threshold
    )

	SELECT @CRERepoDrawTableBody = (
        SELECT 
    		td = FORMAT(joined.TransDate,'d','us'),
    		td = joined.FamilyDealName, 
    		td = FORMAT(joined.lrTrAmt, '#,###'), 
    		td = FORMAT(joined.crTrAmt, '#,###'),
    		td = FORMAT(joined.crTrAmt - joined.lrTrAmt, '#,###')
    	FROM
    	(
    		SELECT 
    			MONTH(lr.TransDate) AS [CurrentMonth],
    			lr.FamilyDealName, 
    			lr.TrAmt AS 'lrTrAmt',
    			cr.TrAmt AS 'crTrAmt',
    			lr.TransDate--,
                --ROW_NUMBER() OVER (PARTITION BY MONTH(lr.TransDate) ORDER BY lr.TransDate DESC) AS RowNum
    		FROM
    		(
    			SELECT 
    				FamilyDealName, 
    				SUM(Amount) AS 'TrAmt',
    				TransDate
    			FROM [BSM].dbo.TransactionEntryArchive ta
    			INNER JOIN [BSM].dbo.Loan l ON l.LoanID = ta.PeopleSoftID
    			WHERE 
    				AuditDate = @auditdate AND 
    				AssetStatus = 'Lending' AND 
    				TransDate >= @sdate AND 
    				TransDate <= @pend AND 
    				ta.TransactionType IN ('Loan Financing Draw', 'CMBS Financing Draw')
    			GROUP BY FamilyDealName, TransDate
    		) lr
    		LEFT JOIN
    		(
    			SELECT 
    				FamilyDealName, 
    				SUM(Amount) AS 'TrAmt',
    				TransDate
    			FROM [BSM].dbo.TransactionEntry ta
    			INNER JOIN [BSM].dbo.Loan l ON l.LoanID = ta.PeopleSoftID
    			WHERE 
    				TransDate >= @sdate AND 
    				TransDate <= @pend AND 
    				ta.TransactionType IN ('Loan Financing Draw', 'CMBS Financing Draw')
    			GROUP BY FamilyDealName, TransDate
    		) cr ON lr.familydealname = cr.familydealname AND lr.TransDate = cr.TransDate
    		WHERE 
    			cr.TrAmt - lr.TrAmt <> 0 
    	) AS joined
    	INNER JOIN RepoDrawDeltas RDD ON RDD.CurrentMonth = joined.CurrentMonth
        --WHERE joined.RowNum <= 3
    	ORDER BY joined.TransDate
	    FOR XML RAW('tr'), ELEMENTS
    )
	SET @CRERepoDrawTableTail = '</table><br><br>' ;
    SELECT  @CRERepoDrawTableBody = @CRERepoDrawTableHead + ISNULL(@CRERepoDrawTableBody, '') + @CRERepoDrawTableTail


    Set @Body = @Body + @LiquiditySummaryTableBody + @CRELoanPdwnTableBody + @CRELoanFFTableBody + @CRERepoPdwnTableBody + @CRERepoDrawTableBody
	Set @Body = @Body + '</body></html>'

    Declare @subject nvarchar(Max)='TEST - Liquidity Projected Soft Close' --'(' + @envName + ')' + ' : 

    Declare @ToRecipients nvarchar(256), 
		    @copy_recipients nvarchar(Max),
		    @blind_copy_recipients nvarchar(Max)

    --Select @ToRecipients = Value from AM..EmailConfiguration where Env = @envName and [Key] = 'ExpMaturityVarianceToRecipient' 
    --Select @copy_recipients = Value from AM..EmailConfiguration where Env = @envName and [Key] = 'ExpMaturityVarianceCCRecipient'
    --Select @blind_copy_recipients = Value from AM..EmailConfiguration where Env = @envName and [Key] = 'ExpMaturityVarianceBCCRecipient'

    --EXEC msdb.dbo.sp_addrolemember @rolename = 'DatabaseMailUserRole'
    --,@membername = 'LNR\jchiou';

    EXEC msdb.dbo.sp_send_dbmail
    @profile_name = 'Sandbox', --'LNR'
    @subject = @subject,
    @recipients = 'jchiou@lnrproperty.com', --@ToRecipients,
    @copy_recipients = 'sdufays@lnrproperty.com',
    --@blind_copy_recipients = @blind_copy_recipients,
    @body = @Body ,
    @body_format = 'HTML' ;
   