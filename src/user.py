from faker import Faker
import pyodbc
import random
from utils import loadConfig

class User:
    def __init__(self, count, config_path='config.yaml'):
        """ User class object for user data.

        Args:
            count (int): The number of user generated.
        """
        self.count = count
        self.fake = Faker()
        self.user_data = self.generate_user()
        self.config = loadConfig(config_path)
    
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
    
    def tosql(self):
        """Insert user data into SQL database using pyodbc.

        Args:
            conn_str (string): a string for connection, make sure to test if its correct
        """
        server = self.config["SERVER"]
        database = self.config["DATABASE"]
        conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;'
        
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