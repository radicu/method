from faker import Faker
import mysql.connector
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
        """Insert user data into MySQL database using mysql.connector.
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
            query = "INSERT INTO User (Name, Email, TradeId, RoleId, CreateDate) VALUES (%s, %s, %s, %s, NOW())"
            for user in self.user_data:
                cursor.execute(query, (user['name'], user['email'], user['trade'], user['role']))
                
            conn.commit()
            
            print("Users inserted successfully.")

            conn.close()

        except mysql.connector.Error as e:
            print("Error connecting to MySQL:", e)
