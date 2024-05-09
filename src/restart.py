import pyodbc
import pandas as pd

from utils import loadConfig
from user import User

def execute_sql_script(config):
    server = config["SERVER"]
    database = config["DATABASE"]
    script_file = config["RESTART_SCRIPT"]

    conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;'
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        with open(script_file, 'r') as file:
            sql_script = file.read()

        cursor.execute(sql_script)
        conn.commit()
        print("SQL script executed successfully.")
        
    except Exception as e:
        print("Error executing SQL script:", e)
        
    finally:
        if conn:
            conn.close()
            
def df_to_sqlserver(df, config):
    server = config["SERVER"]
    database = config["DATABASE"]
    table_name = config["WEATHER_TABLE"]

    conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;'

    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = ?", (table_name,))
        table_exists = cursor.fetchone()[0] > 0

        if not table_exists:
            raise ValueError(f"Table '{table_name}' does not exist. Aborting the operation.")
        
        for _, data in df.iterrows():
            cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE Date = ? AND Hour = ?", (data['Date'],data['Hour']))
            date_exists = cursor.fetchone()[0] > 0
            
            if date_exists:
                query = f"""
                    UPDATE {table_name}
                    SET Temperature = ?,
                        RainProb = ?,
                        WindSpeed = ?,
                        HeavyWeather = ?
                    WHERE Date = ? and Hour = ?
                """
                cursor.execute(query, (data['Temperature'], data['RainProb'], data['WindSpeed'], data['HeavyWeather'], data['Date'], data['Hour']))
            else:
                query = f"""
                    INSERT INTO {table_name} (Date, Hour, Temperature, RainProb, WindSpeed, HeavyWeather)
                    VALUES (?, ?, ?, ?, ?, ?)
                """
                cursor.execute(query, (data['Date'], data['Hour'], data['Temperature'], data['RainProb'], data['WindSpeed'], data['HeavyWeather']))
            
            conn.commit()
        
        print("All weather data successfully moved to the database.")
        
        conn.close()

    except pyodbc.Error as e:
        print("Error connecting to SQL Server:", e)

if __name__ == "__main__":
    config = loadConfig('config.yaml')
    weather_path = config["WEATHER_PATH"]

    execute_sql_script(config)
    
    df = pd.read_csv(weather_path)
    df_to_sqlserver(df,config)
    
    user = User(50)
    user.tosql()    
    
    
