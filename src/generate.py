import random
import pandas as pd
import os
import mysql.connector
from datetime import datetime, timedelta
import sys

from project import Project
from utils import loadConfig

def project_generator(config):
    n = config["PROJECT_COUNT"]
    start_date = config["PROJECT_START_DATE"]
    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    
    for i in range(1, n+1):
        offset = random.randint(0, 36)
        task_count = random.randint(80, 150)
        task_branch = 3 if task_count > 120 else 2
        task_interval = task_count // task_branch + random.randint(1, 6)
        
        project_date = start_date + timedelta(weeks=offset * 4)
        
        project = Project(f'project{i}', str(project_date), task_count, task_interval)
        print(f'[{i}/{n}] : ', end='')
        project.tosql()

def save_data(config):
    server = config["SERVER"]
    database = config["DATABASE"]
    user = config['USERNAME']
    password = config["PASSWORD"]
    port = config["PORT"]
    data_dir = config["DATA_DIR"]

    try:
        conn = mysql.connector.connect(
            host=server,
            port=port,
            database=database,
            user=user,
            password=password
        )
        cursor = conn.cursor()

        task_query = "SELECT * FROM task"
        cursor.execute(task_query)
        tasks = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])

        project_query = "SELECT * FROM project"
        cursor.execute(project_query)
        projects = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])

        conn.close()

        print("SQL script executed successfully.")
        dir_name = str(config["PROJECT_COUNT"]) + '_' + config["PROJECT_START_DATE"][:4]
        dir_path = os.path.join(data_dir, dir_name)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        
        task_path = os.path.join(dir_path, 'task.csv')
        project_path = os.path.join(dir_path, 'project.csv')
        tasks.to_csv(task_path, index=False)
        projects.to_csv(project_path, index=False)
        
        print(f'All data saved at {dir_path}')

    except mysql.connector.Error as e:
        print("Error connecting to MySQL:", e)
        sys.exit(1)

if __name__ == "__main__":
    config = loadConfig('config.yaml')
    project_generator(config)
    save_data(config)
