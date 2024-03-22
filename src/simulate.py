import pandas as pd 
import numpy as np
import sys
import os
from datetime import datetime, timedelta
import pyodbc
import random

from utils import isWorkday, estEndDate, isParentCompleted, isWeekend, calculate_depth, delay

DATA_DIR = 'data'
DEFAULT_CONNECTION_STRING = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=LAPTOP-2NSE0JH1\\SQLEXPRESS;DATABASE=dummy;Trusted_Connection=yes;'

def fromcsv(task_path, project_path):
    tasks = pd.read_csv(os.path.join(DATA_DIR, task_path))
    projects = pd.read_csv(os.path.join(DATA_DIR, project_path))
    return tasks, projects

def fromsql(connection_string, save=False):
    try:
        conn = pyodbc.connect(connection_string)

        cursor = conn.cursor()

        task_query = "SELECT * FROM Task"
        tasks = pd.read_sql(task_query, conn)

        project_query = "SELECT * FROM Project"
        projects = pd.read_sql(project_query, conn)

        conn.close()

    except pyodbc.Error as e:
        print("Error connecting to SQL Server:", e)
        
    if save:
        tasks.to_csv(os.path.join(DATA_DIR, 'tasks.csv'))
        projects.to_csv(os.path.join(DATA_DIR, 'projects.csv'))
    
    return tasks, projects

def read_data():
    if len(sys.argv) < 2:
        print("Usage: python src/simulate.py [csv|sql] [task_path/connection_string] [project_path (for csv)]")
        sys.exit(1)

    data_source = sys.argv[1]

    if data_source == 'csv':
        if len(sys.argv) != 4:
            print("Usage: python src/simulate.py csv [task_path] [project_path]")
            sys.exit(1)
        task_path = sys.argv[2]
        project_path = sys.argv[3]
        tasks, projects = fromcsv(task_path, project_path)
    elif data_source == 'sql':
        if len(sys.argv) < 2:
            print("Usage: python src/simulate.py sql [save] [connection_string]")
            sys.exit(1)

        save = bool(sys.argv[2]) if len(sys.argv) > 2 else False
        connection_string = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_CONNECTION_STRING
        tasks, projects = fromsql(connection_string, save)
    else:
        print("Invalid data source. Please use 'csv' or 'sql'.")
        sys.exit(1)

    return tasks, projects

if __name__ == "__main__":
    tasks, projects = read_data()
    
    tasks['ParentTaskID'] = tasks['ParentTaskID'].astype('Int64') 
    tasks['StartDate'] = pd.to_datetime(tasks['StartDate'])
    tasks['EndDate'] = pd.to_datetime(tasks['EndDate'])
    tasks['ActualStartDate'] = pd.to_datetime(tasks['ActualStartDate'])
    tasks['ActualEndDate'] = pd.to_datetime(tasks['ActualEndDate'])
    
    curr_date = tasks['StartDate'].min()
    task_report = []
    project_report = []

    while ~tasks['Status'].eq('Completed').all():
        task_today = tasks[(tasks['StartDate'] <= curr_date) & (tasks['Status']!='Completed')]['ID'].tolist()

        for idx in task_today:
            task = tasks.loc[tasks['ID']==idx].iloc[0]
            workday = projects.loc[projects['ID'] == task['ProjectID']].iloc[0]['Workday']
            if isParentCompleted(task, tasks) and isWorkday(curr_date, workday):
                if task['Status'] == 'Not Started':
                    task['ActualStartDate'] = str(curr_date)
                    task['Status'] = 'On Progress'
                    
                if delay(task, tasks, task_today, curr_date):
                    task['Progress'] += 0
                else:
                    task['Progress'] += 1
                    
                if task['Progress'] >= task['Duration']:
                    task['ActualEndDate'] = curr_date
                    task['Status'] = 'Completed'
                
                if curr_date > task['EndDate'] and task['Status'] == 'On Progress':
                    task['Status'] = 'Delayed'
                    task['Priority'] = 'Critical'
                
                tasks.loc[tasks['ID']==idx] = task.values
                
                task_report.append({
                    'Date': curr_date,
                    'ID': task['ID'],
                    'Name': task['Name'],
                    'StartDate': task['StartDate'],
                    'EndDate': task['EndDate'],
                    'Cost': task['Cost'],
                    'Priority': task['Priority'],
                    'Progress': task['Progress'],
                    'ProjectID' : task['ProjectID'],
                    'Status': task['Status'],
                    'Duration': task['Duration'],
                    'Trade' : task['Trade'],
                    'ActualStartDate': task['ActualStartDate'],
                    'ActualEndDate': task['ActualEndDate']
                })
                
        for pid in projects['ID'].tolist():
            project_task = tasks[tasks['ProjectID']==pid]
            if ~project_task['Status'].eq('Not Started').all() and ~project_task['Status'].eq('Completed').all():
                project_report.append({
                    'Date' : curr_date,
                    'ProjectID' : pid,
                    'TotalTask' : len(project_task),
                    'StartedTask' : len(project_task[project_task['Status']!='Not Started']),
                    'OnGoingTask' : len(project_task[(project_task['Status']!='Not Started') & (project_task['Status']!='Completed')]),
                    'DelayedTask' : len(project_task[(project_task['Status']=='Delayed')]),
                    'CompletedTask' : len(project_task[(project_task['Status']=='Completed')]),
                    'WorkDay' : project_task[(project_task['Status']!='Not Started')]['Progress'].sum(),
                    'TotalSpent' : project_task[(project_task['Status']=='Completed')]['Cost'].sum()
                })

        curr_date += timedelta(days=1)

    task_reports = pd.DataFrame(task_report)
    project_reports = pd.DataFrame(project_report)
    task_reports['ActualEndDate'] = task_reports.groupby('ID')['ActualEndDate'].bfill()
    task_ns = tasks.copy()
    task_ns['ActualStartDate'] = task_ns['StartDate']
    task_ns['Date'] = task_ns['ActualStartDate']
    task_ns['Priority'] = task_ns.apply(lambda x: 'Critical' if pd.isna(x['ParentTaskID']) else 'Normal', axis=1)
    task_ns['Progress'] = 0
    task_ns['Status'] = 'Not Started'
    task_ns.drop(['ParentTaskID', 'AssigneeID', 'CreateDate'],axis=1, inplace=True)
    task_reports = pd.concat([task_reports, task_ns]).reset_index(drop=True)

    project_dates = tasks.groupby('ProjectID').agg({'StartDate': 'min', 'EndDate': 'max', 'ActualStartDate':'min','ActualEndDate':'max'}).reset_index()
    project_reports = pd.merge(project_reports, project_dates, on='ProjectID', how='left')
    project_ns = project_reports.copy()
    project_ns = project_reports.groupby('ProjectID').agg({'TotalTask':'max','StartDate':'max','EndDate':'max','ActualStartDate':'max','ActualEndDate':'max'}).reset_index()
    project_ns['Date'] = project_ns['ActualStartDate']
    project_ns[['StartedTask','OnGoingTask','DelayedTask','CompletedTask', 'WorkDay', 'TotalSpent']] = 0
    project_reports = pd.concat([project_reports,project_ns]).reset_index(drop=True)

    print(f'Complete all task at {curr_date}')

    task_reports.to_csv(os.path.join(DATA_DIR, 'task_report.csv'),index=False)
    project_reports.to_csv(os.path.join(DATA_DIR, 'project_report.csv'),index=False)
    
    
    

    