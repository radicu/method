from faker import Faker
import mysql.connector
import random
from datetime import datetime, timedelta
from utils import loadConfig, estEndDate

class Project:
    def __init__(self, name, start_date, task_count, task_interval, workday=None, config_path='config.yaml'):
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
        self.config = loadConfig(config_path)
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
        task_data['trade'] = random.randint(22,37) if isLarge else random.randint(1,22)
        task_data['workerScore'] = random.randint(30, 100)
        
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
    
    def tosql(self):
        """ Insert project data into MySQL database using mysql.connector.

        Args:
            conn_str (string): a string for connection, make sure to test if its correct
        """
        server = self.config["SERVER"]
        database = self.config["DATABASE"]
        user = self.config["USERNAME"]
        password = self.config["PASSWORD"]
        port = self.config["PORT"]

        try:
            conn = mysql.connector.connect(
                host=server,
                port=port,
                database=database,
                user=user,
                password=password
            )
            cursor = conn.cursor()
            
            query = "INSERT INTO Project (Name, Status, Workday, AssigneeID, CreateDate) VALUES (%s, %s, %s, %s, NOW())"
            cursor.execute(query, (self.project_data['name'], self.project_data['status'], self.project_data['workday'], self.project_data['assignee']))
            conn.commit()
            
            project_id = cursor.lastrowid
            
            query = "INSERT INTO Task (Name, StartDate, ParentTaskID, Cost, Priority, Progress, ProjectID, Status, Duration, AssigneeID, Trade, CreateDate, WorkerScore) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW() ,%s)"
            prev_task = None
            for task in self.project_data['tasks']:
                if task['priority'] == 'Critical' : 
                    cursor.execute(query, (task['name'], task['startDate'], None, task['cost'], task['priority'], task['progress'], project_id, task['status'], task['duration'], task['assignee'], task['trade'], task['workerScore']))
                    conn.commit()
                else :
                    cursor.execute(query, (task['name'], task['startDate'], prev_task, task['cost'], task['priority'], task['progress'], project_id, task['status'], task['duration'], task['assignee'], task['trade'], task['workerScore']))
                    conn.commit()
                
                prev_task = cursor.lastrowid
            
            print("Project and tasks inserted successfully.")

            conn.close()

        except mysql.connector.Error as e:
            print("Error connecting to MySQL:", e)
