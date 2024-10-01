DROP TABLE IF EXISTS Task;
DROP TABLE IF EXISTS Project;
DROP TABLE IF EXISTS User;
DROP TABLE IF EXISTS Trade;
DROP TABLE IF EXISTS Weather;
DROP TABLE IF EXISTS Role;

CREATE TABLE Role (
    ID INT PRIMARY KEY AUTO_INCREMENT,
    Name VARCHAR(100),
    CreateDate DATE
);

CREATE TABLE Trade (
    ID INT PRIMARY KEY AUTO_INCREMENT,
    Name VARCHAR(100),
    CreateDate DATE
);

CREATE TABLE User (
    ID INT PRIMARY KEY AUTO_INCREMENT,
    Name VARCHAR(100),
    Email VARCHAR(255),
    RoleID INT,
    TradeID INT,
    CreateDate DATE,
    FOREIGN KEY (RoleID) REFERENCES Role(ID),
    FOREIGN KEY (TradeID) REFERENCES Trade(ID)
);

CREATE TABLE Project (
    ID INT PRIMARY KEY AUTO_INCREMENT,
    Name VARCHAR(100),
    Status VARCHAR(10) CHECK (Status IN ('Active', 'Archived')),
    Workday INT CHECK (Workday >= 0 AND Workday <= 127),
    AssigneeID INT,
    CreateDate DATE,
    FOREIGN KEY (AssigneeID) REFERENCES User(ID)
);

CREATE TABLE Task (
    ID INT PRIMARY KEY AUTO_INCREMENT,
    Name VARCHAR(100),
    StartDate DATE,
    EndDate DATE GENERATED ALWAYS AS (DATE_ADD(StartDate, INTERVAL Duration DAY)) VIRTUAL,
    ParentTaskID INT,
    Cost DECIMAL(18, 2),
    Priority VARCHAR(10) CHECK (Priority IN ('Critical', 'Normal')),
    Progress INT CHECK (Progress >= 0 AND Progress <= 100),
    ProjectID INT,
    ActualStartDate DATE,
    ActualEndDate DATE,
    Status VARCHAR(20) CHECK (Status IN ('Not Started', 'In Progress', 'Delayed', 'Completed')),
    Duration INT,
    AssigneeID INT,
    Trade INT,
    CreateDate DATE,
    WorkerScore INT,
    FOREIGN KEY (ProjectID) REFERENCES Project(ID),
    FOREIGN KEY (ParentTaskID) REFERENCES Task(ID),
    FOREIGN KEY (AssigneeID) REFERENCES User(ID)
);

CREATE TABLE Weather (
    Date DATE,
    Hour FLOAT,
    Temperature FLOAT,
    RainProb FLOAT,
    WindSpeed FLOAT,
    HeavyWeather INT
);

INSERT INTO Role (Name, CreateDate)
VALUES 
    ('Head Contractor', CURDATE()),
    ('Admin', CURDATE()),
    ('Contract Administrator', CURDATE()),
    ('Development Manager', CURDATE()),
    ('Project Manager', CURDATE()),
    ('Site Manager', CURDATE()),
    ('Foreman', CURDATE()),
    ('Subcontractor', CURDATE()),
    ('Client Representative', CURDATE());

INSERT INTO Trade (Name, CreateDate)
VALUES 
    ('Tiler', CURDATE()),
    ('Line Marker', CURDATE()),
    ('Landscaper', CURDATE()),
    ('Surveyor', CURDATE()),
    ('Project Manager', CURDATE()),
    ('Painter', CURDATE()),
    ('Reinforcement Fixer', CURDATE()),
    ('Post Tension', CURDATE()),
    ('Plumber', CURDATE()),
    ('Cleaner', CURDATE()),
    ('Plasterboarder', CURDATE()),
    ('Joiner', CURDATE()),
    ('Excavation', CURDATE()),
    ('Concretor', CURDATE()),
    ('Waterproofer', CURDATE()),
    ('Site Manager', CURDATE()),
    ('Floor Sealer', CURDATE()),
    ('Fire', CURDATE()),
    ('Window', CURDATE()),
    ('Mechanical', CURDATE()),
    ('Head Contractor', CURDATE()),
    ('Development Manager', CURDATE()),
    ('Scaffolder', CURDATE()),
    ('Hoarding', CURDATE()),
    ('Carpenter', CURDATE()),
    ('Admin', CURDATE()),
    ('Renderer', CURDATE()),
    ('Contract Administrator', CURDATE()),
    ('Carpet', CURDATE()),
    ('Electrician', CURDATE()),
    ('Stone Mason', CURDATE()),
    ('Timber Floorer', CURDATE()),
    ('Metal Work', CURDATE()),
    ('Foreman', CURDATE()),
    ('Formworker', CURDATE());
