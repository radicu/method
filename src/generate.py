from faker import Faker
import sys
import pyodbc
import random
from datetime import datetime, timedelta

from utils import isWorkday, estEndDate, User, Project

DEFAULT_CONNECTION_STRING = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=LAPTOP-2NSE0JH1\\SQLEXPRESS;DATABASE=dummy;Trusted_Connection=yes;'

def project_generator(n, start_date, connection_string):
    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    for i in range(1,n+1):
        offset = random.randint(0,10)
        task_count = random.randint(10, 50)
        task_branch = 3 if task_count > 30 else 2
        task_interval = task_count // task_branch + random.randint(1,6)
        
        project_date = start_date + timedelta(days=offset*7)
        
        project = Project(f'project{i}', str(project_date), task_count, task_interval)
        print(f'[{i}/{n}] : ', end='')
        project.tosql(connection_string)
        
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python src/generate.py <project_count> <start_date> [<connection_string>]")
        sys.exit(1)

    project_count = sys.argv[1]
    start_date = sys.argv[2]
    connection_string = sys.argv[2] if len(sys.argv) >= 4 else DEFAULT_CONNECTION_STRING

    project_generator(int(project_count), start_date, connection_string)