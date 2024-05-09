import random
import pandas as pd
import os
import pyodbc
from datetime import datetime, timedelta

from project import Project
from utils import loadConfig

def project_generator(config):
    n = config["PROJECT_COUNT"]
    start_date = config["PROJECT_START_DATE"]
    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    
    for i in range(1,n+1):
        offset = random.randint(0,36)
        task_count = random.randint(80, 150)
        task_branch = 3 if task_count > 120 else 2
        task_interval = task_count // task_branch + random.randint(1,6)
        
        project_date = start_date + timedelta(weeks=offset*4)
        
        project = Project(f'project{i}', str(project_date), task_count, task_interval)
        print(f'[{i}/{n}] : ', end='')
        project.tosql()
        
def save_data(config):
    server = config["SERVER"]
    database = config["DATABASE"]
    data_dir = config["DATA_DIR"]
    conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;'
    
    try:
        conn = pyodbc.connect(conn_str)

        cursor = conn.cursor()

        task_query = "SELECT * FROM Task"
        tasks = pd.read_sql(task_query, conn)

        project_query = "SELECT * FROM Project"
        projects = pd.read_sql(project_query, conn)

        conn.close()

    except pyodbc.Error as e:
        print("Error connecting to SQL Server:", e)
        
    dir_name = str(config["PROJECT_COUNT"]) + '_' + config["PROJECT_START_DATE"][:4]
    dir_path = os.path.join(data_dir,dir_name)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    
    task_path = os.path.join(dir_path,'task.csv')
    project_path = os.path.join(dir_path,'project.csv')
    tasks.to_csv(task_path,index=False)
    projects.to_csv(project_path,index=False)
    
    print(f'All data saved at {dir_path}')
        
if __name__ == "__main__":
    config = loadConfig('config.yaml')
    project_generator(config)
    save_data(config)