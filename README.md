# Task and Project delay forecasting

This repository contains the development work of the Angusta System AI Team on project and task delay prediction using AI techniques.

## Directory Structure

- **data/**: Contains generated data for simulation and analysis.
  - the format is **type**_**reports or no**_**num of project**_**optional revision**
  - e.g. project_reports_10  : the project report for the 10 project generated data
  - e.g. task_30 : the task details of all the task in the30 project generated data

- **src/**: Scripts for data generation, SQL initialization, and utilities.
  - **initDB.sql**: SQL script to initialize the SQL environment. It is written for SQL Server; adjustments may be needed for other DBMS.
  - **restartDB.sql**: Script to restart the content of all data in the initialized DB. **Note:** Use `restart.py` instead.
  - **restart.py**: Python script to execute `restartDB.sql`. Accepts the filename and connection string to the database using pyodbc.
    Usage: 
``` bash
python src/restart.py <script_file> [<connection_string>]
```
  - **utils.py**: Python script containing utility functions and classes.
  - **generate.py**: Python script to populate database tables with generated data. Accepts the number of projects, start date, maximum offset in weeks, and connection string as arguments.
    Usage:
``` bash
python src/generate.py <project_count> <start_date> [<connection_string>]
```

- **generation.ipynb**: Deprecated. General workflow to populate database tables.
- **simulation.ipynb**: Notebook for simulating generated data to collect reports. Can use data from CSV files or from the database. The result includes task_reports for daily reports of tasks and project_reports for daily reports of projects.
- **task_model.ipynb**: Notebook for task delay prediction model development. It involves feature engineering, visualization, and model evaluation based on task_reports CSV file as input.
- **project_model.ipynb**: Notebook for project delay prediction model development. It includes feature engineering, visualization, and model evaluation based on project_reports CSV file as input.

## Usage

1. **Initialize SQL Database** 
Run the `src/initDB.sql` or use the python script `restart.py` if already initialized.
2. **Populate Tables with Generated Data**
Run the `src/generate.py` to populate the tables with generated data.
3. **Simulate Project Progression and Collect Reports Data**
Walk through the `simulation.ipynb` to simulate project progression then collect reports data for tasks and projects.
4. **Use Feature Engineering and Develop ML Methods**
Walk through the `task_model.ipynb` and `project_model.ipynb` for feature engineering and develop model.