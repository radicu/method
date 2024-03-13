/*
DROP TABLE IF EXISTS Task;
DROP TABLE IF EXISTS Project;
DROP TABLE IF EXISTS [User];
DROP TABLE IF EXISTS Trade;
DROP TABLE IF EXISTS Role;
DROP FUNCTION dbo.GetAdjustedEndDate;
DROP FUNCTION dbo.GetWorkdayPattern;
*/

CREATE FUNCTION dbo.GetAdjustedEndDate (@StartDate DATE, @Duration INT, @Workday INT)
RETURNS DATE
AS
BEGIN
    DECLARE @EndDate DATE;
    DECLARE @RemainingDuration INT = @Duration;
    DECLARE @CurrentDate DATE = @StartDate;

    WHILE @RemainingDuration - 1 > 0
    BEGIN
        SET @CurrentDate = DATEADD(DAY, 1, @CurrentDate);

        -- Check if the current date is a workday according to the project's workday pattern
        IF (@Workday & POWER(2, (DATEPART(WEEKDAY, @CurrentDate) + 5) % 7)) <> 0
        BEGIN
            SET @RemainingDuration = @RemainingDuration - 1;
        END
    END

    SET @EndDate = @CurrentDate;
    RETURN @EndDate;
END;

CREATE FUNCTION dbo.GetWorkdayPattern(@ProjectID INT)
RETURNS INT
AS
BEGIN
    DECLARE @WorkdayPattern INT;
    SELECT @WorkdayPattern = Workday FROM Project WHERE ID = @ProjectID;
    RETURN @WorkdayPattern;
END;

CREATE TABLE Role (
    ID INT PRIMARY KEY IDENTITY(1,1),
    Name NVARCHAR(100),
    CreateDate Date
);

CREATE TABLE Trade (
    ID INT PRIMARY KEY IDENTITY(1,1),
    Name NVARCHAR(100),
    CreateDate DATE
);

CREATE TABLE [User] (
    ID INT PRIMARY KEY IDENTITY(1,1),
    Name NVARCHAR(100),
    Email NVARCHAR(255),
    RoleID INT,
    TradeID INT,
    CreateDate DATE,
    CONSTRAINT FK_Role FOREIGN KEY (RoleID) REFERENCES Role(ID),
    CONSTRAINT FK_Trade FOREIGN KEY (TradeID) REFERENCES Trade(ID)
);

CREATE TABLE Project (
    ID INT PRIMARY KEY IDENTITY(1,1),
    Name NVARCHAR(100),
    Status NVARCHAR(10) CHECK (Status IN ('Active', 'Archived')),
    Workday INT CHECK (Workday >= 0 AND Workday <= 127),
    AssigneeID INT,
	CreateDate DATE,
    CONSTRAINT FK_Assignee FOREIGN KEY (AssigneeID) REFERENCES [User](ID)
);

CREATE TABLE Task (
    ID INT PRIMARY KEY IDENTITY(1,1),
    Name NVARCHAR(100),
    StartDate DATE,
    EndDate AS dbo.GetAdjustedEndDate(StartDate, Duration, dbo.GetWorkdayPattern(ProjectID)),
    ParentTaskID INT,
    Cost DECIMAL(18, 2),
    Priority NVARCHAR(10) CHECK (Priority IN ('Critical', 'Normal')),
    Progress INT CHECK (Progress >= 0 AND Progress <= 100),
    ProjectID INT,
    ActualStartDate DATE,
    ActualEndDate DATE,
    Status NVARCHAR(20) CHECK (Status IN ('Not Started', 'In Progress', 'Delayed', 'Completed')),
    Duration INT,
    AssigneeID INT,
    CreateDate DATE,
    CONSTRAINT FK_Project FOREIGN KEY (ProjectID) REFERENCES Project(ID),
    CONSTRAINT FK_ParentTask FOREIGN KEY (ParentTaskID) REFERENCES Task(ID),
    CONSTRAINT FK_Assignee_Task FOREIGN KEY (AssigneeID) REFERENCES [User](ID)
);

INSERT INTO Role (Name, CreateDate)
VALUES 
    ('Head Contractor', GETDATE()),
    ('Admin', GETDATE()),
    ('Contract Administrator', GETDATE()),
    ('Development Manager', GETDATE()),
    ('Project Manager', GETDATE()),
    ('Site Manager', GETDATE()),
    ('Foreman', GETDATE()),
    ('Subcontractor', GETDATE()),
    ('Client Representative', GETDATE());

INSERT INTO Trade (Name, CreateDate)
VALUES 
    ('Tiler', GETDATE()),
    ('Line Marker', GETDATE()),
    ('Landscaper', GETDATE()),
    ('Surveyor', GETDATE()),
    ('Project Manager', GETDATE()),
    ('Painter', GETDATE()),
    ('Reinforcement Fixer', GETDATE()),
    ('Post Tension', GETDATE()),
    ('Plumber', GETDATE()),
    ('Cleaner', GETDATE()),
    ('Plasterboarder', GETDATE()),
    ('Joiner', GETDATE()),
    ('Excavation', GETDATE()),
    ('Concretor', GETDATE()),
    ('Waterproofer', GETDATE()),
    ('Site Manager', GETDATE()),
    ('Floor Sealer', GETDATE()),
    ('Fire', GETDATE()),
    ('Window', GETDATE()),
    ('Mechanical', GETDATE()),
    ('Head Contractor', GETDATE()),
    ('Development Manager', GETDATE()),
    ('Scaffolder', GETDATE()),
    ('Hoarding', GETDATE()),
    ('Carpenter', GETDATE()),
    ('Admin', GETDATE()),
    ('Renderer', GETDATE()),
    ('Contract Administrator', GETDATE()),
    ('Carpet', GETDATE()),
    ('Electrician', GETDATE()),
    ('Stone Mason', GETDATE()),
    ('Timber Floorer', GETDATE()),
    ('Metal Work', GETDATE()),
    ('Foreman', GETDATE()),
    ('Formworker', GETDATE());