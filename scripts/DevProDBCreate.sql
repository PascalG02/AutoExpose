-- Step 1: Create Database if it doesn't exist
BEGIN TRY
    IF NOT EXISTS (SELECT 1 FROM sys.databases WHERE name = 'AutoDB_Pascal')
    BEGIN
        CREATE DATABASE AutoDB_Pascal;
        PRINT 'Database "AutoDB_Pascal" created successfully';
    END
    ELSE
        PRINT 'Database "AutoDB_Pascal" already exists';
END TRY
BEGIN CATCH
    PRINT 'Error creating database: ' + ERROR_MESSAGE();
END CATCH

GO

-- Step 2: Use the new database
USE AutoDB_Pascal;
GO

-- Step 3: Create Table if it doesn't exist
BEGIN TRY
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Auto_User')
    BEGIN
        CREATE TABLE Auto_User (
            ID INT PRIMARY KEY IDENTITY(1,1),
            FullName NVARCHAR(100) NOT NULL,
            Email NVARCHAR(100) UNIQUE NOT NULL,
            CreatedAt DATETIME DEFAULT GETDATE()
        );
        PRINT 'Table "Auto_User" created successfully and being initialized';
    END
    ELSE
        PRINT 'Table "Auto_User" already exists';
END TRY
BEGIN CATCH
    PRINT 'Error creating table: ' + ERROR_MESSAGE();
END CATCH

GO

-- Step 4: Insert Sample Data (Avoid duplication using MERGE)
BEGIN TRY
    MERGE INTO Auto_User AS target
    USING (VALUES
        ('Andile Ntumba', 'andile.ntumba@imagine.com'),
        ('Alice Wonderland', 'alice.wonderland@imagine.com'),
        ('Bobby Bobs', 'bob.bob@bobbed.com'),
        ('James Brown', 'james.brown@player.com')
    ) AS source (FullName, Email)
    ON target.Email = source.Email
    WHEN NOT MATCHED THEN
        INSERT (FullName, Email) VALUES (source.FullName, source.Email);
    PRINT 'Table data inserted or already exists.';
END TRY
BEGIN CATCH
    PRINT 'Error inserting data: ' + ERROR_MESSAGE();
END CATCH
