    -- Step 1: Create Database if it doesn't exist
    IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'MyDatabase')
    BEGIN
        CREATE DATABASE MyDatabase;
        PRINT 'Database "MyDatabase" created successfully.';
    END
    ELSE
    BEGIN
        PRINT 'Database "MyDatabase" already exists.';
    END

    -- Step 2: Use the new database
    USE MyDatabase;

    -- Step 3: Create Table if it doesn't exist
    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Users')
    BEGIN
        CREATE TABLE Users (
            ID INT PRIMARY KEY IDENTITY(1,1),
            Name NVARCHAR(100) NOT NULL,
            Email NVARCHAR(100) UNIQUE NOT NULL,
            CreatedAt DATETIME DEFAULT GETDATE()
        );
        PRINT 'Table "Users" created successfully.';
    END
    ELSE
    BEGIN
        PRINT 'Table "Users" already exists.';
    END

    -- Step 4: Insert Sample Data
    INSERT INTO Users (Name, Email) 
    VALUES 
        ('Alice Johnson', 'alice.johnson@example.com'),
        ('Bob Smith', 'bob.smith@example.com'),
        ('Charlie Brown', 'charlie.brown@example.com');