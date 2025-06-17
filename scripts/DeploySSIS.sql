DECLARE @project_binary VARBINARY(MAX);

-- Set the binary data (to be replaced by workflow)
SET @project_binary = 0x;

BEGIN TRY
    IF EXISTS (SELECT 1 FROM [SSISDB].[catalog].[projects] WHERE [name] = 'TimesheetMigrationV2')
        EXEC [SSISDB].[catalog].[delete_project] 'TimesheetMigrationPacks', 'TimesheetMigrationV2';
    
    EXEC [SSISDB].[catalog].[deploy_project] 
        @folder_name = 'TimesheetMigrationPacks',
        @project_name = 'TimesheetMigrationV2',
        @project_stream = @project_binary;
    
    PRINT 'Deployment successful to server: ' + @@SERVERNAME + ', folder: TimesheetMigrationPacks, project: TimesheetMigrationV2';
END TRY
BEGIN CATCH
    PRINT 'ERROR: ' + ERROR_MESSAGE();
    THROW;
END CATCH
