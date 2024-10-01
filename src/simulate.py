import pandas as pd
import sys
import os
from datetime import timedelta
import mysql.connector
from tqdm import tqdm

from utils import *

def fromcsv(config):
    data_dir = config["DATA_DIR"]
    dir_name = str(config["PROJECT_COUNT"]) + '_' + config["PROJECT_START_DATE"][:4]
    dir_path = os.path.join(data_dir, dir_name)
    
    tasks = pd.read_csv(os.path.join(dir_path, 'task.csv'))
    projects = pd.read_csv(os.path.join(dir_path, 'project.csv'))
    return tasks, projects

def fromsql(config):
    server = config["SERVER"]
    database = config["DATABASE"]
    user = config['USERNAME']
    password = config["PASSWORD"]
    port = config["PORT"]
    
    try:
        conn = mysql.connector.connect(
            host=server,
            port=port,
            database=database,
            user=user,
            password=password
        )

        cursor = conn.cursor()

        task_query = "SELECT * FROM Task"
        cursor.execute(task_query)
        tasks = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])

        project_query = "SELECT * FROM Project"
        cursor.execute(project_query)
        projects = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])

        conn.close()

    except mysql.connector.Error as e:
        print("Error connecting to MySQL:", e)
    
    return tasks, projects

def read_data(config):
    data_source = config["SIMULATION_SOURCE"]

    if data_source == 'csv':
        tasks, projects = fromcsv(config)
    elif data_source == 'sql':
        tasks, projects = fromsql(config)
    else:
        print("Invalid data source. Please use 'csv' or 'sql'.")
        sys.exit(1)
    
    return tasks, projects

def read_historical(config):
    historical_path = config["WEATHER_HISTORICAL_PATH"]
    df = pd.read_csv(historical_path)
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df.set_index('datetime')
    return df

def preprocess_task(tasks, weather_historical, projects):
    tasks['ParentTaskID'] = tasks['ParentTaskID'].astype('Int64')
    tasks['StartDate'] = pd.to_datetime(tasks['StartDate'])
    tasks['EndDate'] = pd.to_datetime(tasks['EndDate'])
    tasks['ActualStartDate'] = pd.to_datetime(tasks['ActualStartDate'])
    tasks['ActualEndDate'] = pd.to_datetime(tasks['ActualEndDate'])
    
    def get_weather_assessment(row):
        start_date = row['StartDate']
        project_id = row['ProjectID']
        workday = projects.loc[projects['ID'] == project_id, 'Workday'].iloc[0]
        weather_assessment = assessWeather(start_date, workday, weather_historical)
        print(f"Weather assessment for Task ID {row['ID']} on Start Date {start_date}: {weather_assessment}")
        return weather_assessment

    tasks['WeatherAssessment'] = tasks.apply(get_weather_assessment, axis=1)
    
    tasks['TaskLength'] = calcLength(tasks['ParentTaskID'])
    if 'Trade' not in tasks.columns:
        tasks['Trade'] = ''
    return tasks

def simulate_one_day(curr_date, tasks, projects, task_report, project_report, weather_historical):
    task_today = tasks[(tasks['StartDate'] <= curr_date) & (tasks['Status'] != 'Completed')]['ID'].tolist()
    heavy_weather = isHeavyWeather(curr_date, weather_historical)
    temperature, rain_prob, wind_speed = getWeatherVariable(curr_date, weather_historical)

    for idx in task_today:
        task = tasks.loc[tasks['ID'] == idx].iloc[0]
        workday = projects.loc[projects['ID'] == task['ProjectID']].iloc[0]['Workday']
        if isParentCompleted(task, tasks):
            if task['Status'] == 'Not Started':
                task['ActualStartDate'] = str(curr_date)
                task['Status'] = 'On Progress'

            if isWorkday(curr_date, workday):
                if delay(task, task_today, curr_date, temperature, rain_prob, wind_speed):
                    task['Progress'] += 0
                else:
                    task['Progress'] += 1

            if task['Progress'] >= task['Duration']:
                task['ActualEndDate'] = curr_date
                task['Status'] = 'Completed'
                pbar.update(1)

            if curr_date > task['EndDate'] and task['Status'] == 'On Progress':
                task['Status'] = 'Delayed'
                task['Priority'] = 'Critical'

            tasks.loc[tasks['ID'] == idx] = task.values

            task_report.append({
                'Date': curr_date,
                'ID': task['ID'],
                'Name': task['Name'],
                'StartDate': task['StartDate'],
                'EndDate': task['EndDate'],
                'Cost': task['Cost'],
                'Priority': task['Priority'],
                'Progress': task['Progress'],
                'ProjectID': task['ProjectID'],
                'Status': task['Status'],
                'Duration': task['Duration'],
                'Trade': task['Trade'],
                'TaskLength': task['TaskLength'],
                'Temperature': temperature,
                'RainProb': rain_prob,
                'WindSpeed': wind_speed,
                'WorkerScore': task['WorkerScore'],
                'IsBadWeather': heavy_weather,
                'WeatherAssessment': task['WeatherAssessment'],
                'WorkDay': workday,
                'ActualStartDate': task['ActualStartDate'],
                'ActualEndDate': task['ActualEndDate']
            })

    for pid in projects['ID'].tolist():
        project_task = tasks[tasks['ProjectID'] == pid]
        if ~project_task['Status'].eq('Not Started').all() and ~project_task['Status'].eq('Completed').all():
            project_report.append({
                'Date': curr_date,
                'ProjectID': pid,
                'TotalTask': len(project_task),
                'StartedTask': len(project_task[project_task['Status'] != 'Not Started']),
                'OnGoingTask': len(project_task[(project_task['Status'] != 'Not Started') & (project_task['Status'] != 'Completed')]),
                'DelayedTask': len(project_task[(project_task['Status'] == 'Delayed')]),
                'CompletedTask': len(project_task[(project_task['Status'] == 'Completed')]),
                'WorkDay': project_task[(project_task['Status'] != 'Not Started')]['Progress'].sum(),
                'TotalSpent': project_task[(project_task['Status'] == 'Completed')]['Cost'].sum(),
                # 'IsBadWeather': heavy_weather,
    
            })

    return

def save_report(config, task_reports, project_reports):
    data_dir = config["DATA_DIR"]
    dir_name = str(config["PROJECT_COUNT"]) + '_' + config["PROJECT_START_DATE"][:4]
    dir_path = os.path.join(data_dir, dir_name)
    
    task_reports.to_csv(os.path.join(dir_path, 'task_report.csv'), index=False)
    project_reports.to_csv(os.path.join(dir_path, 'project_report.csv'), index=False)
    print(f'Simulation result saved at {dir_path}')
    
    return

if __name__ == "__main__":
    config = loadConfig('config.yaml')
    tasks, projects = read_data(config)
    weather_historical = read_historical(config)
    tasks = preprocess_task(tasks, weather_historical, projects)
    print('Read data successful')
    
    curr_date = tasks['StartDate'].min()
    task_report = []
    project_report = []

    total_tasks = len(tasks)
    pbar = tqdm(total=total_tasks, desc="Progress")

    while ~tasks['Status'].eq('Completed').all():
        simulate_one_day(curr_date, tasks, projects, task_report, project_report, weather_historical)
        curr_date += timedelta(days=1)

    task_reports = pd.DataFrame(task_report)
    project_reports = pd.DataFrame(project_report)
    task_reports['ActualEndDate'] = task_reports.groupby('ID')['ActualEndDate'].bfill()

    project_dates = tasks.groupby('ProjectID').agg({'StartDate': 'min', 'EndDate': 'max', 'ActualStartDate': 'min', 'ActualEndDate': 'max'}).reset_index()
    project_dates['WeatherAssessment'] = project_dates.apply(lambda x: assessWeather(x['StartDate'], projects.loc[projects['ID'] == x['ProjectID']]['Workday'].iloc[0], weather_historical), axis=1)
    project_reports = pd.merge(project_reports, project_dates, on='ProjectID', how='left')
    
    print(f'Complete all tasks at {curr_date}')
    pbar.close()
    
    save_report(config, task_reports, project_reports)
