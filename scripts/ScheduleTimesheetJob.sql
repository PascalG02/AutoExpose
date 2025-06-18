USE msdb;
GO

-- Check if the job already exists and delete it to avoid conflicts
IF EXISTS (SELECT job_id FROM msdb.dbo.sysjobs WHERE name = N'RunTimesheetMigration')
BEGIN
    EXEC msdb.dbo.sp_delete_job @job_name = N'RunTimesheetMigration', @delete_unused_schedule = 1;
END
GO

-- Create the SQL Server Agent job
DECLARE @jobId BINARY(16);
EXEC msdb.dbo.sp_add_job
    @job_name = N'RunTimesheetMigration',
    @enabled = 1,
    @description = N'Job to execute LoadTimesheet.dtsx SSIS package every minute',
    @owner_login_name = N'sa', -- Replace with appropriate login if needed
    @job_id = @jobId OUTPUT;

-- Add a job step to execute the SSIS package
EXEC msdb.dbo.sp_add_jobstep
    @job_id = @jobId,
    @step_name = N'Execute LoadTimesheet SSIS Package',
    @step_id = 1,
    @subsystem = N'SSIS',
    @command = N'/ISSERVER "\"\SSISDB\TimesheetMigration\TimesheetMigrationV2\LoadTimesheets.dtsx\"" /SERVER "\".\""',
    @on_success_action = 1, -- Quit with success
    @on_fail_action = 2; -- Quit with failure

-- Add a schedule to run every minute
EXEC msdb.dbo.sp_add_jobschedule
    @job_id = @jobId,
    @name = N'EveryMinuteSchedule',
    @enabled = 1,
    @freq_type = 4, -- Daily
    @freq_interval = 1,
    @freq_subday_type = 4, -- Minute
    @freq_subday_interval = 1, -- Every 1 minute
    @active_start_date = 20250618,
    @active_end_date = 99991231,
    @active_start_time = 000000; -- Start at midnight

-- Assign the job to the target server
EXEC msdb.dbo.sp_add_jobserver
    @job_id = @jobId,
    @server_name = N'(local)'; -- Adjust if targeting a remote server
GO