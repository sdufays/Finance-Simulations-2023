--CREATE PROCEDURE [dbo].[usp_ProcessPIDForCLO]
--    @pid NVARCHAR(MAX) -- actual parameter inputted
--AS

--BEGIN
    DECLARE @pid NVARCHAR(MAX) = 'LT0100' -- testing only
    --select * from FinancingBUSetup where LID = 94

    SET NOCOUNT ON;

    DECLARE @lid INT, 
    @bu NVARCHAR(MAX), 
    @ppsplit DECIMAL(28, 15), 
    @clo_end_date DATETIME, 
    @clo_reinvestment_period_end DATETIME, 
    @LoanMaturityDate DATETIME,
    @loan_pdwn_amt DECIMAL(28, 15),
    @clo_bal DECIMAL(28, 15),
    @residual_amt DECIMAL(28, 15),
    @repo_name NVARCHAR(MAX),
    @repo_draw_amt DECIMAL(28, 15),
    @financing_bal_sum DECIMAL(28, 15);
    
    -- Lookup correct LID
    set @lid = (select n.LID from [ILAS].dbo.Note n 
                            inner join [ILSCommon].dbo.NoteCalc nc on nc.LID = n.LID
                    where nc.ScenarioID = 2 and n.PID = @pid)
    
    -- check if PID is pledged to a CLO
    IF EXISTS (SELECT 1 FROM [ILAS].dbo.FinancingBUSetup WHERE [FinancingSourceName] LIKE '%CLO%' AND LID = @lid)
    BEGIN
        -- PID is pledged to a CLO, proceed with algorithm
        SELECT 
            @bu = [BusinessUnit], 
            @ppsplit = PariPassuSplit, 
            @clo_end_date = [MaturityDateUsed],
            @clo_reinvestment_period_end = 
                CASE 
                    WHEN [FinancingSourceName] = 'STWD 2021 - SIF1 CLO' THEN '2024-04-06'
                    WHEN [FinancingSourceName] = 'STWD 2021 - SIF2 CLO' THEN '2025-01-10'
                    ELSE NULL
                END
        FROM [ILAS].dbo.FinancingBUSetup
        WHERE LID = @lid

        -- Run multiple times for each PID + BU combo ----

        -- STEP 2: identify the expected maturity date of the loan
        SELECT @LoanMaturityDate = MaturityDateUsed
        FROM [ILAS].dbo.MaturitySchedule ms
        INNER JOIN [ILSCommon].dbo.NoteCalc nc ON ms.LID = nc.LID
        WHERE ms.LID = @lid AND nc.ScenarioID = 2 AND ms.ScheduleType = 'Expected Maturity date';

        -- PROCESS 2: no action if loan’s maturity is prior to CLO Reinvestment Period End Date
        IF @LoanMaturityDate <= @clo_reinvestment_period_end
        BEGIN
            -- exit algorithm (is this how u stop a stored procedure?)
            RETURN;
        END

        -- PROCESS 3: end of reinvestment, before deal call
        IF @LoanMaturityDate > @clo_reinvestment_period_end AND @LoanMaturityDate <= @clo_end_date
        BEGIN
            -- get loan paydown amount
            SELECT @loan_pdwn_amt = [BeginningBalance] * @ppsplit
            FROM [ILSCommon].dbo.PeriodEndData
            WHERE [PeriodEndDate] = EoMonth(@LoanMaturityDate, 0) 
                and ScenarioID = 2
                
            -- get loan balance
            SELECT @clo_bal = [BeginningBalance]
            FROM [ILSCommon].dbo.FinancingPeriodEndDataBU
            WHERE [PeriodEndDate] = EoMonth(@LoanMaturityDate, 0) 
                and ScenarioID = 2 
                and BusinessUnit = @bu

            -- find residual
            SET @residual_amt = @loan_pdwn_amt - @clo_bal;

            -- create joined table that only includes ScenarioID2
            -- but join with Note to get PID
            WITH FinancingBalanceData AS (
                SELECT 
                    fped.LID,
                    n.PID AS [PID], 
                    SUM(fped.BeginningBalance) AS [FinancingBalance], -- sum of loan balances for the PID
                    MAX(fbs.FinancingSourceName) AS [FinancingSourceName], -- CLO name, should all be same for same PID
                    @residual_amt * SUM(BeginningBalance) AS [AllocatedNotDivided]
                FROM [ILAS].dbo.FinancingBUSetup fbs
                    INNER JOIN [ILAS].dbo.Note n ON fbs.LID = n.LID
                    INNER JOIN [ILSCommon].dbo.NoteCalc nc ON fbs.LID = nc.LID
                    INNER JOIN [ILSCommon].dbo.FinancingPeriodEndDataBU fped ON fbs.LID = fped.LID
                WHERE nc.ScenarioID = 2 
                    AND fped.PeriodEndDate = EoMonth(@LoanMaturityDate, 0) 
                    AND fped.BusinessUnit = @bu
                    AND fbs.FinancingSourceName = @repo_name
                GROUP BY n.PID, fped.LID
            )
            -- get sum of all balances for this PID
            SELECT 
                @financing_bal_sum = (SELECT SUM(FinancingBalance)
            FROM FinancingBalanceData
            GROUP BY FinancingSourceName);

            -- insert into table
            -- Multiple Loan IDs that belong to that CLO and currently active (not the subject LID)
            -- Date: Subject PID maturity date
            -- RepoLineName = CLO name
            INSERT INTO [ILAS].dbo.ProjectedRepoTransactions ([LID], [Date], [RepoLineName], [Comments], [Amount])
            SELECT
                LID AS [LID],
                @LoanMaturityDate AS [Date],
                FinancingSourceName AS [RepoLineName],
                @lid AS [Comments],
                AllocatedNotDivided / @financing_bal_sum AS [Amount]
            FROM FinancingBalanceData

        END

        -- PROCESS 4: rollover after termination date
        IF @LoanMaturityDate > @clo_end_date
        BEGIN
            SELECT @clo_bal = [BeginningBalance]
            FROM [ILSCommon].dbo.FinancingPeriodEndDataBU
            WHERE [PeriodEndDate] = EoMonth(@clo_end_date, 0) 
                and ScenarioID = 2 
                and BusinessUnit = @bu

            INSERT INTO [ILAS].dbo.ProjectedRepoTransactions ([LID], [Date], [RepoLineName], [Comments], [Amount])
            SELECT
                @lid AS [LID],
                @LoanMaturityDate AS [Date],
                FinancingSourceName AS [RepoLineName],
                @lid AS [Comments],
                @clo_bal AS [Amount];

            -- date must be = termination date for this
            IF @LoanMaturityDate = @clo_end_date
            BEGIN
                SELECT
                    @repo_name = [FinancingSourceName]
                FROM [ILAS].dbo.FinancingBUSetup

                IF @repo_name = 'DB Repo'
                BEGIN
                    SET @repo_draw_amt = @clo_bal * 0.85
                END
                ELSE IF @repo_name = 'MUFG Repo' OR @repo_name = 'BANA'
                BEGIN
                    SET @repo_draw_amt = @clo_bal * 0.825
                END
            END
        END
    END


