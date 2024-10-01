import pandas as pd
import yaml
import random
from datetime import datetime, timedelta

weather_all = pd.read_csv('data/weather/weather_all.csv')
weather_all['datetime'] = pd.to_datetime(weather_all['datetime'])
weather_all = weather_all.set_index('datetime')

def loadConfig(file_path):
    with open(file_path, "r") as file:
        config = yaml.safe_load(file)
    return config

def isWorkday(date, workday):
    return (workday & pow(2, date.weekday())) != 0

def assessWeather(start_date, workday, weather_data=weather_all):
    end_date = start_date + timedelta(days=7)
    select_weather = weather_data[start_date:end_date]
    count = 0
    warning = 0

    for date, row in select_weather.iterrows():
        if isWorkday(date, workday):
            if row['HeavyWeather'] == 1:
                warning += 1
            count += 1

    if count == 0:
        return 0
    return warning / count * 100

def isHeavyWeather(curr_date, weather_data=weather_all):
    return weather_data.loc[curr_date]['HeavyWeather']

def getWeatherVariable(curr_date, weather_data=weather_all):
    Temperature = format(weather_data.loc[curr_date]['Temperature'], '.3f')
    RainProb = format(weather_data.loc[curr_date]['RainProb'], '.3f')
    WindSpeed = format(weather_data.loc[curr_date]['WindSpeed'], '.3f')

    return Temperature, RainProb, WindSpeed


def estEndDate(start_date, duration, workday):
    if isinstance(start_date, str):
        curr_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    else:
        curr_date = start_date
        
    remaining = duration 
    while remaining-1 > 0:
        curr_date += timedelta(days=1)
        if isWorkday(curr_date, workday):
            remaining -= 1
    
    return curr_date

def calcLength(series):
    task_list = [0]*len(series)
    for i, pid in enumerate(series):
        if pd.isna(pid):
            task_list[i] = 0
        else:
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
    
def delay(task, task_today, curr_date, temperature, rain_prob, wind_speed):
    # const_weather = -2 if heavy_weather else 0
    # const_weather2 = -2 if (float(temperature) <= -10) or (float(rain_prob) >= 70) or (float(wind_speed) >= 55) else 0
    const_temperature = -1 if float(temperature) else 0
    const_rainProb = -1 if float(rain_prob) else 0
    const_windSpeed = -1 if float(wind_speed) else 0
    # const_count = -2 if len(task_today) >= 10 else 0
    const_date = -1 if isWeekend(curr_date) else 0
    # const_status = 2 if task['Priority'] == 'Critical' else 0
    const_trade = -2 if task['Trade'] <= 22 else 0
    const_cost = -1 if task['Cost'] <= 800 else 0
    const_worker = -1 if task['WorkerScore'] <= 50 else 0


    #Original Delay without const_count
    denom = 8 + const_temperature + const_rainProb + const_windSpeed  + const_date + const_trade + const_cost + const_worker 


    #Original Delay
    # denom = 10 + const_temperature + const_rainProb + const_windSpeed + const_count + const_date + const_trade + const_cost + const_worker 

    #Without status
    # denom = 6 + const_trade + const_cost + const_date + const_count + const_weather

    #Delay with weather2
    # denom = 6 + const_trade + const_cost + const_date + const_count + const_weather2

    #Delay with worker Score
    # denom = 7 + const_trade + const_cost + const_date + const_count + const_weather2 + const_worker
    
    # denom = max(denom,3)
    
    # return random.randint(1,denom) == 1

    #Adjsuted
    return random.randint(1, denom) == 1 if denom > 0 else True  # Always delay if denom <= 0


def delay2(task, task_today, curr_date, heavy_weather):
    const_weather = -2 if heavy_weather else 0
    const_count = -2 if len(task_today) >= 10 else 0
    const_date = -1 if isWeekend(curr_date) else 0
    const_status = 2 if task['Priority'] == 'Critical' else 0
    const_trade = 1 if task['Trade'] >= 3 else -1
    const_cost = 1 if task['Cost'] >= 800 else -1
    denom = 8 + const_status + const_trade + const_cost + const_date + const_count + const_weather
    
    denom = max(denom,3)
    
    return random.randint(1,denom) == 1

