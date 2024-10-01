import mysql.connector
import pandas as pd

from utils import loadConfig
from user import User

def execute_sql_script(config):
    server = config["SERVER"]
    database = config["DATABASE"]
    user = config['USERNAME']
    password = config["PASSWORD"]
    port = config["PORT"]
    script_file = config["RESTART_SCRIPT"]

    try:
        conn = mysql.connector.connect(
            host=server,
            port=port,
            database=database,
            user=user,
            password=password
        )
        cursor = conn.cursor()

        with open(script_file, 'r') as file:
            sql_script = file.read()

        for result in cursor.execute(sql_script, multi=True):
            pass

        conn.commit()
        print("SQL script executed successfully.")

    except mysql.connector.Error as e:
        print("Error executing SQL script:", e)

    finally:
        if conn:
            conn.close()

def df_to_mysql(df, config):
    server = config["SERVER"]
    database = config["DATABASE"]
    user = config["USERNAME"]
    password = config["PASSWORD"]
    port = config["PORT"]
    table_name = config["WEATHER_TABLE"]

    try:
        conn = mysql.connector.connect(
            host=server,
            port=port,
            database=database,
            user=user,
            password=password
            
        )
        cursor = conn.cursor()
        
        cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
        table_exists = cursor.fetchone() is not None

        if not table_exists:
            raise ValueError(f"Table '{table_name}' does not exist. Aborting the operation.")
        
        for _, data in df.iterrows():
            cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE Date = %s AND Hour = %s", (data['Date'],data['Hour']))
            date_exists = cursor.fetchone()[0] > 0
            
            if date_exists:
                query = f"""
                    UPDATE {table_name}
                    SET Temperature = %s,
                        RainProb = %s,
                        WindSpeed = %s,
                        HeavyWeather = %s
                    WHERE Date = %s and Hour = %s
                """
                cursor.execute(query, (data['Temperature'], data['RainProb'], data['WindSpeed'], data['HeavyWeather'], data['Date'], data['Hour']))
            else:
                query = f"""
                    INSERT INTO {table_name} (Date, Hour, Temperature, RainProb, WindSpeed, HeavyWeather)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query, (data['Date'], data['Hour'], data['Temperature'], data['RainProb'], data['WindSpeed'], data['HeavyWeather']))
            
            conn.commit()
        
        print("All weather data successfully moved to the database.")
        
        conn.close()

    except mysql.connector.Error as e:
        print("Error connecting to MySQL:", e)

if __name__ == "__main__":
    config = loadConfig('config.yaml')
    weather_path = config["WEATHER_PATH"]

    execute_sql_script(config)
    
    df = pd.read_csv(weather_path)
    df_to_mysql(df, config)
    
    user = User(50)
    user.tosql()
