import sys
import pyodbc
from utils import User

DEFAULT_CONNECTION_STRING = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=LAPTOP-2NSE0JH1\\SQLEXPRESS;DATABASE=dummy;Trusted_Connection=yes;'

def execute_sql_script(connection_string, script_file):
    try:
        conn = pyodbc.connect(connection_string)
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

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python src/restart.py <script_file> [<connection_string>]")
        sys.exit(1)

    script_file = sys.argv[1]
    connection_string = sys.argv[2] if len(sys.argv) >= 3 else DEFAULT_CONNECTION_STRING

    execute_sql_script(connection_string, script_file)
    
    user = User(50)
    user.tosql(connection_string)    
    
    
