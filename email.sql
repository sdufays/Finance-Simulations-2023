declare @pend as datetime = '3-31-2024'
declare @sdate as datetime = '6-15-2023'
declare @auditdate as datetime = '6-15-2023'
declare @moend as datetime = EoMonth(@sdate)
declare @mostart as datetime
declare @lm_balance decimal(28, 15), @ff_delta decimal(28, 15), @pdwn_delta decimal(28, 15)
declare @repodraw_delta decimal(28, 15), @repopdwn_delta decimal(28, 15), @total_delta decimal(28, 15)
DECLARE @threshold DECIMAL(18, 2)
SET @threshold = 5000000

declare @Body NVARCHAR(MAX),
@LiquiditySummaryTableBody NVARCHAR(MAX),
@LiquiditySummaryTableHead VARCHAR(1000),
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

DECLARE @FFLargeDeltaInfo TABLE (
    FamilyDealName VARCHAR(50),
    lr_Tramt DECIMAL(18, 2),
    cr_Tramt DECIMAL(18, 2)
);


IF OBJECT_ID('tempdb..#LiquiditySummary') IS NOT NULL
    DROP TABLE #LiquiditySummary
CREATE TABLE #LiquiditySummary(PeriodEndDate datetime, MoEndBalance decimal(28, 15), Lending_FFChange decimal(28, 15),
                            Lending_LoanPdwnChange decimal(28, 15), Lending_RepoDrawChange decimal(28, 15), 
							Lending_RepoPdwnChange decimal(28, 15), 
                            Updated_MoEndBalance decimal(28, 15)
                            )

WHILE @moend <= EoMonth(@pend, 0)
BEGIN
    set @mostart = (select case when @moend = EoMonth(@sdate, 0) then @sdate else EoMonth(@moend, -1) end)
    -- month end balance from most recent liquidity report:
    set @lm_balance = (select Amount from [BSM].dbo.TransactionEntryArchive ta
                    where AuditDate = @auditdate and TransactionType = 'Month End Cash + AUD Low Point'
                        and TransDate = @moend);
    
    -- change from loan ff projections
    -- define the CTE to join lr and cr tables
    WITH JoinedTable AS (
        -- select FamilyDealName and sum of amount columns
        SELECT lr.FamilyDealName, lr.TrAmt AS 'lr_Tramt', cr.TrAmt AS 'cr_Tramt'
        FROM (
            -- select FamilyDealName and sum of amount columns
            SELECT FamilyDealName, SUM(Amount) AS 'TrAmt'
            FROM [BSM].dbo.TransactionEntryArchive ta
            INNER JOIN [BSM].dbo.Loan l ON l.LoanID = ta.PeopleSoftID
            WHERE AuditDate = @auditdate
                AND AssetStatus = 'Lending'
                AND TransDate > @mostart
                AND TransDate <= @moend
                AND ta.TransactionType = 'Loan Future Funding'
            GROUP BY FamilyDealName
        ) lr -- archived table alias
        LEFT JOIN -- join with current table alias
        (
            -- get same columns
            SELECT FamilyDealName, SUM(Amount) AS 'TrAmt'
            FROM [BSM].dbo.TransactionEntry ta
            INNER JOIN [BSM].dbo.Loan l ON l.LoanID = ta.PeopleSoftID
            WHERE TransDate > @mostart
                AND TransDate <= @moend
                AND ta.TransactionType = 'Loan Future Funding'
            GROUP BY FamilyDealName -- Group to deal level
        ) cr ON lr.familydealname = cr.familydealname
    ) -- group on FamilyDealName

    -- use CTE to calculate ff_delta
    SELECT @ff_delta = SUM(cr_Tramt - lr_Tramt)
    FROM JoinedTable;


    --IF ABS(@ff_delta) > 5000000
    --BEGIN
    --    INSERT INTO @FFLargeDeltaInfo (FamilyDealName, lr_Tramt, cr_Tramt)
    --    SELECT FamilyDealName, lr_Tramt, cr_Tramt
    --    FROM JoinedTable;
    --END


    -- change from loan pdwn projections
    set @pdwn_delta = (select SUM(cr.TrAmt - lr.TrAmt) as 'LiquidityImpact'
    from
        (
        select FamilyDealName, SUM(Amount) as 'TrAmt'
        from [BSM].dbo.TransactionEntryArchive ta
            inner join [BSM].dbo.Loan l on l.LoanID = ta.PeopleSoftID
        where AuditDate = @auditdate and AssetStatus = 'Lending' and TransDate > @mostart and TransDate <= @moend
            and (ta.TransactionType = 'Loan Curtailment' or ta.TransactionType = 'Loan Balloon Payment' or ta.TransactionType = 'CMBS Curtailment')
        group by FamilyDealName
        ) lr
    left join
        (
        select FamilyDealName, SUM(Amount) as 'TrAmt'
        from [BSM].dbo.TransactionEntry ta
            inner join [BSM].dbo.Loan l on l.LoanID = ta.PeopleSoftID
        where TransDate > @mostart and TransDate <= @moend
            and (ta.TransactionType = 'Loan Curtailment' or ta.TransactionType = 'Loan Balloon Payment' or ta.TransactionType = 'CMBS Curtailment')
        group by FamilyDealName
        ) cr on lr.familydealname = cr.familydealname
    )

    -- change from repo draw projections
    set @repodraw_delta = (select SUM(cr.TrAmt - lr.TrAmt) as 'LiquidityImpact'
    from
        (
        select FamilyDealName, SUM(Amount) as 'TrAmt'
        from [BSM].dbo.TransactionEntryArchive ta
            inner join [BSM].dbo.Loan l on l.LoanID = ta.PeopleSoftID
        where AuditDate = @auditdate and AssetStatus = 'Lending' and TransDate > @mostart and TransDate <= @moend
            and (ta.TransactionType = 'Loan Financing Draw' or ta.TransactionType = 'CMBS Financing Draw')
        group by FamilyDealName
        ) lr
    left join
        (
        select FamilyDealName, SUM(Amount) as 'TrAmt'
        from [BSM].dbo.TransactionEntry ta
            inner join [BSM].dbo.Loan l on l.LoanID = ta.PeopleSoftID
        where TransDate > @mostart and TransDate <= @moend
            and (ta.TransactionType = 'Loan Financing Draw' or ta.TransactionType = 'CMBS Financing Draw')
        group by FamilyDealName
        ) cr on lr.familydealname = cr.familydealname
    )

    -- change from repo pdwn projections
    set @repopdwn_delta = (select SUM(cr.TrAmt - lr.TrAmt) as 'LiquidityImpact'
    from
        (
        select FamilyDealName, SUM(Amount) as 'TrAmt'
        from [BSM].dbo.TransactionEntryArchive ta
            inner join [BSM].dbo.Loan l on l.LoanID = ta.PeopleSoftID
        where AuditDate = @auditdate and AssetStatus = 'Lending' and TransDate > @mostart and TransDate <= @moend
            and (ta.TransactionType = 'Loan Financing Curtailment' or ta.TransactionType = 'CMBS Financing curtailment')
        group by FamilyDealName
        ) lr
    left join
        (
        select FamilyDealName, SUM(Amount) as 'TrAmt'
        from [BSM].dbo.TransactionEntry ta
            inner join [BSM].dbo.Loan l on l.LoanID = ta.PeopleSoftID
        where TransDate > @mostart and TransDate <= @moend
            and (ta.TransactionType = 'Loan Financing Curtailment' or ta.TransactionType = 'CMBS Financing curtailment')
        group by FamilyDealName
        ) cr on lr.familydealname = cr.familydealname
    )

    -- TODO:
    -- if any delta > threshold
    -- save the delta and the month to a table, and get the influential transactions in that category for that date
    -- save lm_amount
    -- select X from [BSM].dbo.TransactionEntryArchive where TransDate = @moend and AuditDate = @auditdate

    set @total_delta = isnull(@total_delta, 0) + @ff_delta + @pdwn_delta + isnull(@repodraw_delta, 0) - isnull(@repopdwn_delta, 0)

    INSERT INTO #LiquiditySummary(PeriodEndDate, MoEndBalance, Lending_FFChange, Lending_LoanPdwnChange, 
                            Lending_RepoDrawChange, Lending_RepoPdwnChange, 
                            Updated_MoEndBalance
                            )
    VALUES(@moend, @lm_balance, @ff_delta, @pdwn_delta, 
            @repodraw_delta, -@repopdwn_delta, 
            @lm_balance + @total_delta)
            
    set @moend = EOMONTH(@moend, 1)
END

SET @Body = '<html><head>Projected liquidity month end cash + approved undrawn balance using most recent liquidity report as of ' + CAST(FORMAT(@auditdate, 'd', 'us') as nvarchar) + 
                ' as a starting point and adding changing in cash flows projections from Lending Segment' + '<style>'
		+ 'table {border-collapse: collapse; font-family: Calibri, Arial, sans-serif;} '
		+ 'td {border: solid black; border-width: 1px; padding: 5px; font: 11px Arial;} '
		+ 'th {background-color: #E6E6FA; font-weight: bold; text-align: center; padding: 5px;} '
		+ '.light-red {background-color: #FFCCCC; color: white;} '
		+ '.medium-red {background-color: #FF9999; color: white;} '
		+ '.strong-red {background-color: #FF6666; color: white;} '
		+ '</style>' + '</head>' + '<body>'

    SET @LiquiditySummaryTableHead = ''
        + ' <br> <table cellpadding=5 cellspacing=0 border=1>' 
        + '<tr>'
		+ '<th><b>Month End</b></th>'
		+ '<th><b>Mo End Cash + AUD Balance from Liquidity Report</b></th>'
		+ '<th><b>Lending - Change in Loan Funding projections</b></th>'
		+ '<th><b>Lending - Change in Loan Pdwn projections</b></th>'
        + '<th><b>Lending - Change in Repo Draw projections</b></th>'
        + '<th><b>Lending - Change in Repo Pdwn projections</b></th>'
        + '<th><b>Projected Mo End Cash + AUD Balance</b></th>'
        + '<th><b>Cumulative Liquidity Impact from changes in projections for Lending segment</b></th>'
		+ '<tr>'

    SET @LiquiditySummaryTableBody = (select td = FORMAT(PeriodEndDate, 'd', 'us'), 
                                td = FORMAT(MoEndBalance, '#,###'), 
                                -- apply conditional formatting highlighting for when delta is really big
                                td = CASE
                                    WHEN ABS(Lending_FFChange) > 8000000 THEN '<span class="strong-red">' + FORMAT(Lending_FFChange, '#,###') + '</span>'
                                    WHEN ABS(Lending_FFChange) > 6000000 THEN '<span class="medium-red">' + FORMAT(Lending_FFChange, '#,###') + '</span>'
                                    WHEN ABS(Lending_FFChange) > 4000000 THEN '<span class="light-red">' + FORMAT(Lending_FFChange, '#,###') + '</span>'
                                    ELSE FORMAT(Lending_FFChange, '#,###')
                                END,
                                td = FORMAT(Lending_LoanPdwnChange, '#,###'),
                                td = FORMAT(Lending_RepoDrawChange, '#,###'), 
                                td = FORMAT(Lending_RepoPdwnChange, '#,###'), 
                                td = FORMAT(Updated_MoEndBalance, '#,###'),
                                td = FORMAT(Updated_MoEndBalance - MoEndBalance, '#,###')
                        from #LiquiditySummary

					 FOR   XML RAW('tr'),
					  ELEMENTS

					)

    SET @LiquiditySummaryTableTail = '</table><br><br>';
    SELECT  @LiquiditySummaryTableBody = @LiquiditySummaryTableHead + ISNULL(@LiquiditySummaryTableBody, '') + @LiquiditySummaryTableTail;

    SELECT @Body + @LiquiditySummaryTableBody + '</body></html>';
	
     --- Table showing top 10 CRE loans with Pdwn changes:
    SET @CRELoanPdwnTableHead = ''
		+ ' <br> <table cellpadding=0 cellspacing=0 border=0>' 
		+ '<tr><b>Top 10 CRE loans with changes in paydown projections vs prior liquidity report</b></tr>'
		+ '<th><b>Deal Name</b></td>'
		+ '<th><b>Most recent liquidity report</b></td>'
		+ '<th><b>Current data set</b></td>'
		+ '<th><b>Liquidity Impact</b></td>'
		+ '<tr>'

	SET @CRELoanPdwnTableBody = (select top 10 
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
                                        and (ta.TransactionType = 'Loan Curtailment' or ta.TransactionType = 'Loan Balloon Payment' or ta.TransactionType = 'CMBS Curtailment')
                                    group by FamilyDealName
                                    ) lr
                                left join
                                    (
                                    select FamilyDealName, SUM(Amount) as 'TrAmt'
                                    from [BSM].dbo.TransactionEntry ta
                                        inner join [BSM].dbo.Loan l on l.LoanID = ta.PeopleSoftID
                                    where TransDate >= @sdate and TransDate <= @pend
                                        and (ta.TransactionType = 'Loan Curtailment' or ta.TransactionType = 'Loan Balloon Payment' or ta.TransactionType = 'CMBS Curtailment')
                                    group by FamilyDealName
                                    ) cr on lr.familydealname = cr.familydealname
                                where cr.TrAmt - lr.TrAmt <> 0
                                order by abs(cr.TrAmt - lr.TrAmt) desc 

					 FOR   XML RAW('tr'),
					  ELEMENTS

					)
	SET @CRELoanPdwnTableTail = '</table><br><br>' ;
    SELECT  @CRELoanPdwnTableBody = @CRELoanPdwnTableHead + ISNULL(@CRELoanPdwnTableBody, '') + @CRELoanPdwnTableTail

    --- Table showing top 10 CRE loans with FF funding changes:
    SET @CRELoanFFTableHead = ''
		+ ' <br> <table cellpadding=0 cellspacing=0 border=0>' 
		+ '<tr><b>Top 10 CRE loans with changes in funding projections vs prior liquidity report</b></tr>'
		+ '<td bgcolor=#E6E6FA><b>Deal Name</b></td>'
		+ '<td bgcolor=#E6E6FA><b>Most recent liquidity report</b></td>'
		+ '<td bgcolor=#E6E6FA><b>Current data set</b></td>'
		+ '<td bgcolor=#E6E6FA><b>Liquidity Impact</b></td>'
		+ '<tr>'

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
		+ ' <br> <table cellpadding=0 cellspacing=0 border=0>' 
		+ '<tr><b>Top 10 CRE loans with changes in repo paydown projections vs prior liquidity report</b></tr>'
		+ '<td bgcolor=#E6E6FA><b>Deal Name</b></td>'
		+ '<td bgcolor=#E6E6FA><b>Most recent liquidity report</b></td>'
		+ '<td bgcolor=#E6E6FA><b>Current data set</b></td>'
		+ '<td bgcolor=#E6E6FA><b>Liquidity Impact</b></td>'
		+ '<tr>'

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
		+ ' <br> <table cellpadding=0 cellspacing=0 border=0>' 
		+ '<tr><b>Top 10 CRE loans with changes in repo draw projections vs prior liquidity report</b></tr>'
		+ '<td bgcolor=#E6E6FA><b>Deal Name</b></td>'
		+ '<td bgcolor=#E6E6FA><b>Most recent liquidity report</b></td>'
		+ '<td bgcolor=#E6E6FA><b>Current data set</b></td>'
		+ '<td bgcolor=#E6E6FA><b>Liquidity Impact</b></td>'
		+ '<tr>'

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