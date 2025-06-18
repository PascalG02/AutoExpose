-- Create folder if not exists
IF NOT EXISTS (SELECT 1 FROM SSISDB.catalog.folders WHERE name = 'TimesheetMigration')
BEGIN
  EXEC SSISDB.catalog.create_folder @folder_name = 'TimesheetMigration', @folder_id = NULL
END

-- Deploy the package
DECLARE @ProjectBinary VARBINARY(MAX)
SELECT @ProjectBinary = BulkColumn 
FROM OPENROWSET(BULK '$(IspacPath)', SINGLE_BLOB) AS x

EXEC SSISDB.catalog.deploy_project 
  @folder_name = 'TimesheetMigration',
  @project_name = 'TimesheetMigrationV2',
  @project_stream = @ProjectBinary
