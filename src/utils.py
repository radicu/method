from faker import Faker
import numpy as np
import pandas as pd
import pyodbc
import random
from datetime import datetime, timedelta

weather_all = pd.read_csv('data/weather/weather_all.csv')
weather_all['datetime'] = pd.to_datetime(weather_all['datetime'])
weather_all = weather_all.set_index('datetime')

def isWorkday(date, workday):
    return (workday & pow(2, date.weekday())) != 0

def assessWeather(start_date, workday, weather_data=weather_all):
    end_date = start_date + timedelta(days=30)
    select_weather = weather_data[start_date:str(end_date)]
    count = 0
    warning = 0
    
    for date, row in select_weather.iterrows():
        if isWorkday(date, workday) :
            if row['heavy_weather'] == 1:
                warning += 1
            count += 1
    
    return warning/count*100

def isHeavyWeather(curr_date, weather_data=weather_all):
    return weather_data.loc[curr_date]['heavy_weather']

def estEndDate(start_date, duration, workday):
    if isinstance(start_date, str):
        curr_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    else :
        curr_date = start_date
        
    remaining = duration 
    while remaining-1 > 0:
        curr_date += timedelta(days=1)
        if isWorkday(curr_date, workday):
            remaining -= 1
    
    return curr_date

def calcLength(series) :
    task_list = [0]*len(series)
    for i, pid in enumerate(series):
        if pd.isna(pid):
            task_list[i] = 0
        else :
            task_list[i] = task_list[pid-1]+1
    
    return task_list

def isWeekend(date):
    return date.weekday() >= 5

def isParentCompleted(task, tasks):
    if pd.isnull(task['ParentTaskID']):
        return True
    else:
        parent_task = tasks[tasks['ID'] == task['ParentTaskID']].iloc[0]
        return parent_task['Status'] == 'Completed'
    
def delay(task, task_today, curr_date, heavy_weather):
    const_weather = -2 if heavy_weather else 0
    const_count = -2 if len(task_today) >= 10 else 0
    const_date = -1 if isWeekend(curr_date) else 0
    const_status = 2 if task['Priority'] == 'Critical' else 0
    const_trade = 1 if task['Trade'] >= 3 else -1
    const_cost = 1 if task['Cost'] >= 800 else -1
    denom = 8 + const_status + const_trade + const_cost + const_date + const_count + const_weather
    
    denom = max(denom,3)
    
    return random.randint(1,denom) == 1

class User:
    def __init__(self, count):
        """ User class object for user data.

        Args:
            count (int): The number of user generated.
        """
        self.count = count
        self.fake = Faker()
        self.user_data = self.generate_user()
    
    def generate_user(self):
        user_list = []
        for _ in range(self.count):
            user_data = {}
            user_data['name'] = self.fake.name()
            user_data['email'] = self.fake.email()
            user_data['role'] = random.randint(1,9)
            user_data['trade'] = random.randint(1,35)
            
            user_list.append(user_data)
        
        return user_list
    
    def tosql(self, conn_str):
        """Insert user data into SQL database using pyodbc.

        Args:
            conn_str (string): a string for connection, make sure to test if its correct
        """
        try:
            conn = pyodbc.connect(conn_str)

            cursor = conn.cursor()
            query = "INSERT INTO [user] (Name, Email, TradeId, RoleId, CreateDate) VALUES (?, ?, ?, ?, GETDATE())"
            for user in self.user_data:
                cursor.execute(query, (user['name'], user['email'], user['trade'], user['role']))
                
            conn.commit()
            
            print("Users inserted successfully.")

            conn.close()

        except pyodbc.Error as e:
            print("Error connecting to SQL Server:", e)

class Project:
    def __init__(self, name, start_date, task_count, task_interval, workday=None):
        """ Project class object to create project data simulation. A project consisted of several tasks with different start dates and duration.

        Args:
            name (string): string
            start_date (string): starting date of the project, format(%Y-%m-%d)
            task_count (int): the number of generated tasks
            task_interval (int): the longest possible consecutive tasks
            workday (int) : integer representation of workday in a week, leave for random
        """
        self.name = name
        self.start_date = start_date
        self.task_count = task_count
        self.task_interval = task_interval
        self.fake = Faker()
        if workday :
            self.workday = workday
        else :
            self.workday = random.choice([31, 63, 127])
        self.project_data = self.get_project_data()
    
    def get_project_data(self):
        """ Generate the project data and other essential information.

        Returns:
            Dictionary: dictionary of project informations
        """
        project_data = {}
        
        project_data['name'] = self.name
        project_data['status'] = 'Active'
        project_data['workday'] = self.workday
        project_data['assignee'] = 1
        project_data['tasks'] = self.generate_task()
        end_dates = [estEndDate(d['startDate'], d['duration'], self.workday) for d in project_data['tasks']]
        project_data['startDate'] = min(project_data['tasks'], key=lambda x: x['startDate'])['startDate']
        project_data['endDate'] = str(max(end_dates))
        
        return project_data
    
    def generate_task_data(self, start_date, scale):
        """ Generate task data. A task can be classified to a large scale and a small scale, a large scale tasks usually have higher costs and longer durations.

        Args:
            start_date (string): starting date of the task, format(%Y-%m-%d)
            scale (string): the scale of the task, a single lowercase character 'l' if large and 's' if small

        Returns:
            Dictionary: dictionary of task informations
        """
        isLarge = True if scale == 'l' else False
        task_data = {}
        
        task_data['name'] = self.fake.word()
        task_data['startDate'] = start_date
        task_data['cost'] = random.randint(1000,3000) if isLarge else random.randint(200,1000)
        task_data['priority'] = 'Critical' if isLarge else 'Normal'
        task_data['progress'] = 0
        task_data['project'] = self.name
        task_data['status'] = 'Not Started'
        task_data['duration'] = random.randint(8,20) if isLarge else random.randint(2,8)
        task_data['assignee'] = 1
        task_data['trade'] = random.randint(4,7) if isLarge else random.randint(1,4)
        
        return task_data 
    
    def generate_task(self):
        """ Generate a list of tasks. The number of tasks are controlled by self.task_count parameters and generated consecutively to simulate dependencies. 
        The maximum consecutive tasks are controlled by self.task_interval parameter.

        Returns:
            List: a list of generated tasks
        """
        task_list = []
        curr_count = 0
        curr_date = datetime.strptime(self.start_date, '%Y-%m-%d').date()
        
        while self.task_count > 0 :
            if curr_count == 0:
                task = self.generate_task_data(str(curr_date), 'l')
            elif curr_count > 30 :
                if random.randint(1, 50) == 1 and self.task_count>40:
                    task = self.generate_task_data(str(curr_date), 'l')
                    curr_count = 0
                else :
                    task = self.generate_task_data(str(curr_date), 's')
            elif curr_count > 50 :
                if random.randint(1, 25) == 1 and self.task_count>40:
                    task = self.generate_task_data(str(curr_date), 'l')
                    curr_count = 0
                else :
                    task = self.generate_task_data(str(curr_date), 's')
            elif curr_count > 70:
                if random.randint(1, 10) == 1 and self.task_count>40:
                    task = self.generate_task_data(str(curr_date), 'l')
                    curr_count = 0
                else :
                    task = self.generate_task_data(str(curr_date), 's')
            else :
                task = self.generate_task_data(str(curr_date), 's')
            
            task_list.append(task)
            curr_date = estEndDate(curr_date, task['duration'], self.workday) + timedelta(days=random.randint(0,2))
            curr_count += 1
            self.task_count -= 1
            
            if curr_count%self.task_interval == 0:
                curr_count = 0
                curr_date = datetime.strptime(self.start_date, '%Y-%m-%d').date() + timedelta(days=random.randint(0,7))
        
        return task_list
    
    def tosql(self, conn_str):
        """ Insert project data into SQL database using pyodbc.

        Args:
            conn_str (string): a string for connection, make sure to test if its correct
        """
        try:
            conn = pyodbc.connect(conn_str)

            cursor = conn.cursor()
            
            query = "INSERT INTO Project (Name, Status, Workday, AssigneeID, CreateDate) VALUES (?, ?, ?, ?, GETDATE())"
            cursor.execute(query, (self.project_data['name'], self.project_data['status'], self.project_data['workday'], self.project_data['assignee']))   
            cursor.commit()
            
            cursor.execute("SELECT @@IDENTITY AS ProjectID")
            project_id = cursor.fetchone()[0]
            
            query = "INSERT INTO Task (Name, StartDate, ParentTaskID, Cost, Priority, Progress, ProjectID, Status, Duration, AssigneeID, Trade, CreateDate) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())"
            prev_task = None
            for task in self.project_data['tasks']:
                if task['priority'] == 'Critical' : 
                    cursor.execute(query, (task['name'], task['startDate'], None, task['cost'], task['priority'], task['progress'], project_id, task['status'], task['duration'], task['assignee'], task['trade']))
                    cursor.commit()
                else :
                    cursor.execute(query, (task['name'], task['startDate'], prev_task, task['cost'], task['priority'], task['progress'], project_id, task['status'], task['duration'], task['assignee'], task['trade']))
                    cursor.commit()
                
                cursor.execute("SELECT @@IDENTITY AS ProjectID")
                prev_task = cursor.fetchone()[0]
            
            cursor.commit()
            
            print("Project and tasks inserted successfully.")

            conn.close()

        except pyodbc.Error as e:
            print("Error connecting to SQL Server:", e)
    