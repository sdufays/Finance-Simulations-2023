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
    + ' <br><b>Top 10 CRE loans with changes in paydown projections vs prior liquidity report</b>'
    + '<table>'
    + '<tr>'
    + '<th>Transaction Date</th>'
    + '<th>Deal Name</th>'
    + '<th>Most recent liquidity report</th>'
    + '<th>Current data set</th>'
    + '<th>Liquidity Impact</th>'
    + '</tr>'

    SELECT @CRELoanPdwnTableBody = (
	    SELECT 
		    td = lr.TransDate,
		    td = lr.FamilyDealName, 
		    td = FORMAT(lr.TrAmt, '#,###'), 
		    td = FORMAT(cr.TrAmt, '#,###'),
		    td = FORMAT(cr.TrAmt - lr.TrAmt, '#,###')
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
			    (ta.TransactionType = 'Loan Curtailment' OR ta.TransactionType = 'Loan Balloon Payment' OR ta.TransactionType = 'CMBS Curtailment')
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
			    (ta.TransactionType = 'Loan Curtailment' OR ta.TransactionType = 'Loan Balloon Payment' OR ta.TransactionType = 'CMBS Curtailment')
		    GROUP BY FamilyDealName, TransDate
	    ) cr ON lr.familydealname = cr.familydealname AND lr.TransDate = cr.TransDate
	    WHERE 
		    cr.TrAmt - lr.TrAmt <> 0 AND 
		    ABS(cr.TrAmt - lr.TrAmt) > @threshold
	    ORDER BY ABS(cr.TrAmt - lr.TrAmt) DESC
	    FOR XML RAW('tr'), ELEMENTS
    )

	SET @CRELoanPdwnTableTail = '</table><br><br>' ;
    SELECT  @CRELoanPdwnTableBody = @CRELoanPdwnTableHead + ISNULL(@CRELoanPdwnTableBody, '') + @CRELoanPdwnTableTail

    --- Table showing top 10 CRE loans with FF funding changes:
    SET @CRELoanFFTableHead = ''
    + ' <br><b>Top 10 CRE loans with changes in funding projections vs prior liquidity report</b>'
    + '<table>'
    + '<tr>'
    + '<th>Deal Name</th>'
    + '<th>Most recent liquidity report</th>'
    + '<th>Current data set</th>'
    + '<th>Liquidity Impact</th>'
    + '</tr>'

	SET @CRELoanFFTableBody = (select top 10 
                                    td = lr.FamilyDealName, 
                                    td = FORMAT(lr.TrAmt, '#,###'), 
                                    td = FORMAT(cr.TrAmt, '#,###'),
                                    td = FORMAT(cr.TrAmt - lr.TrAmt, '#,###')
                                from
                                    (
                                    select FamilyDealName, SUM(Amount) as 'TrAmt'
                                    from [BSM].dbo.TransactionEntryArchive ta
                                        inner join [BSM].dbo.Loan l on l.LoanID = ta.PeopleSoftID
                                    where AuditDate = @auditdate and AssetStatus = 'Lending' and TransDate >= @sdate and TransDate <= @pend
                                        and ta.TransactionType = 'Loan Future Funding'
                                    group by FamilyDealName
                                    ) lr
                                left join
                                    (
                                    select FamilyDealName, SUM(Amount) as 'TrAmt'
                                    from [BSM].dbo.TransactionEntry ta
                                        inner join [BSM].dbo.Loan l on l.LoanID = ta.PeopleSoftID
                                    where TransDate >= @sdate and TransDate <= @pend
                                        and ta.TransactionType = 'Loan Future Funding'
                                    group by FamilyDealName
                                    ) cr on lr.familydealname = cr.familydealname
                                where cr.TrAmt - lr.TrAmt <> 0
                                order by abs(cr.TrAmt - lr.TrAmt) desc 


					 FOR   XML RAW('tr'),
					  ELEMENTS

					)
	SET @CRELoanFFTableTail = '</table><br><br>' ;
    SELECT  @CRELoanFFTableBody = @CRELoanFFTableHead + ISNULL(@CRELoanFFTableBody, '') + @CRELoanFFTableTail

    --- Table showing top 10 CRE loans with Repo Pdwn changes:
    SET @CRERepoPdwnTableHead = ''
    + ' <br><b>Top 10 CRE loans with changes in repo paydown projections vs prior liquidity report</b>'
    + '<table>'
    + '<tr>'
    + '<th>Deal Name</th>'
    + '<th>Most recent liquidity report</th>'
    + '<th>Current data set</th>'
    + '<th>Liquidity Impact</th>'
    + '</tr>'

	SET @CRERepoPdwnTableBody = (select top 10 
                                    td = lr.FamilyDealName, 
                                    td = FORMAT(lr.TrAmt, '#,###'), 
                                    td = FORMAT(cr.TrAmt, '#,###'),
                                    td = FORMAT(-cr.TrAmt + lr.TrAmt, '#,###')
                                from
                                    (
                                    select FamilyDealName, SUM(Amount) as 'TrAmt'
                                    from [BSM].dbo.TransactionEntryArchive ta
                                        inner join [BSM].dbo.Loan l on l.LoanID = ta.PeopleSoftID
                                    where AuditDate = @auditdate and AssetStatus = 'Lending' and TransDate >= @sdate and TransDate <= @pend
                                        and (ta.TransactionType = 'Loan Financing Curtailment' or ta.TransactionType = 'CMBS Financing curtailment')
                                    group by FamilyDealName
                                    ) lr
                                left join
                                    (
                                    select FamilyDealName, SUM(Amount) as 'TrAmt'
                                    from [BSM].dbo.TransactionEntry ta
                                        inner join [BSM].dbo.Loan l on l.LoanID = ta.PeopleSoftID
                                    where TransDate >= @sdate and TransDate <= @pend
                                        and (ta.TransactionType = 'Loan Financing Curtailment' or ta.TransactionType = 'CMBS Financing curtailment')
                                    group by FamilyDealName
                                    ) cr on lr.familydealname = cr.familydealname
                                where cr.TrAmt - lr.TrAmt <> 0
                                order by abs(cr.TrAmt - lr.TrAmt) desc 

					 FOR   XML RAW('tr'),
					  ELEMENTS

					)
	SET @CRERepoPdwnTableTail = '</table><br><br>' ;
    SELECT  @CRERepoPdwnTableBody = @CRERepoPdwnTableHead + ISNULL(@CRERepoPdwnTableBody, '') + @CRERepoPdwnTableTail

    --- Table showing top 10 CRE loans with Repo Draw changes:
    SET @CRERepoDrawTableHead = ''
    + ' <br><b>Top 10 CRE loans with changes in repo draw projections vs prior liquidity report</b>'
    + '<table>'
    + '<tr>'
    + '<th>Deal Name</th>'
    + '<th>Most recent liquidity report</th>'
    + '<th>Current data set</th>'
    + '<th>Liquidity Impact</th>'
    + '</tr>'

	SET @CRERepoDrawTableBody = (select top 10 
                                    td = lr.FamilyDealName, 
                                    td = FORMAT(lr.TrAmt, '#,###'), 
                                    td = FORMAT(cr.TrAmt, '#,###'),
                                    td = FORMAT(cr.TrAmt - lr.TrAmt, '#,###')
                                from
                                    (
                                    select FamilyDealName, SUM(Amount) as 'TrAmt'
                                    from [BSM].dbo.TransactionEntryArchive ta
                                        inner join [BSM].dbo.Loan l on l.LoanID = ta.PeopleSoftID
                                    where AuditDate = @auditdate and AssetStatus = 'Lending' and TransDate >= @sdate and TransDate <= @pend
                                        and (ta.TransactionType = 'Loan Financing Draw' or ta.TransactionType = 'CMBS Financing Draw')
                                    group by FamilyDealName
                                    ) lr
                                left join
                                    (
                                    select FamilyDealName, SUM(Amount) as 'TrAmt'
                                    from [BSM].dbo.TransactionEntry ta
                                        inner join [BSM].dbo.Loan l on l.LoanID = ta.PeopleSoftID
                                    where TransDate >= @sdate and TransDate <= @pend
                                        and (ta.TransactionType = 'Loan Financing Draw' or ta.TransactionType = 'CMBS Financing Draw')
                                    group by FamilyDealName
                                    ) cr on lr.familydealname = cr.familydealname
                                where cr.TrAmt - lr.TrAmt <> 0
                                order by abs(cr.TrAmt - lr.TrAmt) desc 

					 FOR   XML RAW('tr'),
					  ELEMENTS

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
    --@copy_recipients = @copy_recipients,
    --@blind_copy_recipients = @blind_copy_recipients,
    @body = @Body ,
    @body_format = 'HTML' ;
   