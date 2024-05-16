import os
import pandas as pd

from utils import isWeekend, estEndDate, loadConfig

def read_data(config):
    data_dir = config["DATA_DIR"]
    dir_name = str(config["PROJECT_COUNT"]) + '_' + config["PROJECT_START_DATE"][:4]
    dir_path = os.path.join(data_dir,dir_name)
    
    tasks = pd.read_csv(os.path.join(dir_path, 'task_report.csv'))
    projects = pd.read_csv(os.path.join(dir_path, 'project_report.csv'))
    tasks_detail = pd.read_csv(os.path.join(dir_path, 'task.csv'))
    projects_detail = pd.read_csv(os.path.join(dir_path, 'project.csv'))
    return tasks, tasks_detail, projects, projects_detail

def preprocess_task(df):
    df['Date'] = pd.to_datetime(df['Date'])
    df['StartDate'] = pd.to_datetime(df['StartDate'])
    df['EndDate'] = pd.to_datetime(df['EndDate'])
    df['ActualStartDate'] = pd.to_datetime(df['ActualStartDate'])
    df['ActualEndDate'] = pd.to_datetime(df['ActualEndDate'])
    
    df['Progress'] = df['Progress']/df['Duration']*100
    df['Weekend'] = df['Date'].apply(lambda x: isWeekend(x)).astype(int)
    df['StartDelay'] = (df['ActualStartDate'] - df['StartDate']).dt.days
    df['DayCount'] = (df['Date']-df['ActualStartDate']).dt.days 
    df['TaskDelay'] = df.apply(lambda x: x['ActualEndDate'].date() - estEndDate(x['ActualStartDate'].date(), x['Duration'], x['WorkDay']),axis=1).dt.days

    TaskToday = df.groupby(['Date','ProjectID'])['ID'].count().reset_index(name='TaskToday')
    df = pd.merge(tasks,TaskToday,on=['Date','ProjectID'],how='left')
    return df

def feature_engineering_task(df):
    df['Priority'] = df['Priority'].apply(lambda x: 1 if x=='Critical' else 0)
    status_ohe = pd.get_dummies(df['Status'], prefix='Is').astype(int)
    df = pd.concat([df, status_ohe], axis=1)
    df.drop(columns='Status', inplace=True)
    
    df = df.rename({'Trade':'Worker'},axis=1)
    df = df.drop(columns=['TaskLength','Weekend','DayCount','TaskToday','Is_Completed','Is_On Progress'])
    return df

def preprocess_project(df):
    df['Progress'] = df['CompletedTask']/df['TotalTask']*100

    df['Date'] = pd.to_datetime(df['Date'])
    df['StartDate'] = pd.to_datetime(df['StartDate'])
    df['EndDate'] = pd.to_datetime(df['EndDate'])
    df['ActualStartDate'] = pd.to_datetime(df['ActualStartDate'])
    df['ActualEndDate'] = pd.to_datetime(df['ActualEndDate'])

    df['Weekend'] = df['Date'].apply(lambda x: isWeekend(x)).astype(int)
    df['DayCount'] = (df['Date']-df['ActualStartDate']).dt.days 
    df['Delay'] = (df['ActualEndDate'] - df['EndDate']).dt.days
    return df

if __name__ == "__main__":
    config = loadConfig('config.yaml')
    tasks, tasks_detail, projects, projects_details = read_data(config)
    
    tasks = preprocess_task(tasks)
    tasks_df =  tasks.drop(columns=['Date','ID','ProjectID','Name','StartDate','EndDate','ActualStartDate','ActualEndDate','WorkDay'])
    tasks_df = feature_engineering_task(tasks_df)
    
    projects = preprocess_project(projects)
    projects_df =  projects.drop(columns=['Date','ProjectID','StartDate','EndDate','ActualStartDate','ActualEndDate'])
    projects_df = projects_df.astype(float)
    
    data_dir = config["DATA_DIR"]
    dir_name = str(config["PROJECT_COUNT"]) + '_' + config["PROJECT_START_DATE"][:4]
    dir_path = os.path.join(data_dir,dir_name)
    
    tasks.to_csv(os.path.join(dir_path,'task_data.csv'),index=False)
    tasks_df.to_csv(os.path.join(dir_path,'task_train.csv'),index=False)
    projects.to_csv(os.path.join(dir_path,'project_data.csv'),index=False)
    projects_df.to_csv(os.path.join(dir_path,'project_train.csv'),index=False)
    
    print(f'All processed data is saved at {dir_path}')