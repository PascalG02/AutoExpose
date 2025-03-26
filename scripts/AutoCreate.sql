-- Step 1: Create Database if it doesn't exist
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'Auto_DB')
BEGIN
    CREATE DATABASE Auto_DB;
    PRINT 'Database "Auto_DB" created successfully';
END
ELSE
BEGIN
    PRINT 'Database "Auto_DB" already exists.';
END

GO

-- Step 2: Use the new database
USE Auto_DB;

GO

-- Step 3: Create Table if it doesn't exist
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Auto_User')
BEGIN
    CREATE TABLE Auto_User (
        ID INT PRIMARY KEY IDENTITY(1,1),
        Name NVARCHAR(100) NOT NULL,
        Email NVARCHAR(100) UNIQUE NOT NULL,
        CreatedAt DATETIME DEFAULT GETDATE()
    );
    PRINT 'Table "Auto_User" created successfully and being initialised';
END
ELSE
BEGIN
    PRINT 'Table "Auto_User" already exists';
END

GO

-- Step 4: Insert Sample Data (no check, always runs)
INSERT INTO Auto_User (Name, Email) 
VALUES 
    ('Alice Wonderland', 'alice.wonderland@imagine.com'),
    ('Bobby bobs', 'bob.bob@bobbed.com'),
    ('James Brown', 'james.brown@player.com');
PRINT 'Table data inserted.';
