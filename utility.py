import shap
import numpy as np
from collections import defaultdict, deque
import pandas as pd

class VotingRegressorWrapper:
    def __init__(self, voting_regressor):
        self.voting_regressor = voting_regressor

    def predict(self, X):
        # This returns the ensemble prediction
        return self.voting_regressor.predict(X)

class SHAP_Evaluation:
    def __init__(self, model, df, background_df, model_code):
        self.model = model
        self.df = df
        self.background_def = background_df
        self.model_code = model_code

    def SHAP_Calculation(self):
        #Machine Learning Model
        if self.model_code == 'ML':
            explainer = shap.Explainer(self.model)
            shap_values =  explainer(self.df)

            return shap_values
        
        #Deep Learning model
        elif self.model_code == 'DL':
            explainer = shap.KernelExplainer(self.model.predict, self.background_def)
            shap_values = explainer.shap_values(self.df)
            
            return shap_values
        
        #Ensemble Model
        elif self.model_code == 'EL':
            wrapped_model = VotingRegressorWrapper(self.model)
            explainer = shap.KernelExplainer(wrapped_model.predict, self.df)
            shap_values = explainer.shap_values(self.df)

            return shap_values

    
    def SHAP_Dictionary(self):
        shap_values = self.SHAP_Calculation()

        #For Deep Learning and Ensemble Learning model
        if (self.model_code == 'EL') or (self.model_code == 'DL'):
            shap_values = shap_values.reshape(-1, len(self.df.columns))
            shap_dicts = []
            for row in shap_values:
                shap_dicts.append({col: val for col, val in zip(self.df.columns, row)})
            return shap_dicts
        
        #For Machine Learning model
        elif (self.model_code == 'ML'):
            shap_dicts = []
            for row in shap_values.values:
                shap_dicts.append({col: val for col, val in zip(self.df.columns, row)})

            return shap_dicts

            
def required_column_task():
    
    required_columns = [
            'Duration',
            'Trade',
            'Progress' ,
            'WorkerScore',
            'Temperature',
            'RainProb',
            'WindSpeed',
    ]
     
    return required_columns

def required_column_project():

    required_columns = [
            'Id',
            'Predecessor',
            'Successor',
            'Duration',
            'Trade',
            'Progress' ,
            'WorkerScore',
            'Temperature',
            'RainProb',
            'WindSpeed',
    ]
     
    return required_columns


# Create a graph of tasks and their dependencies
def build_graph(df):
    graph = defaultdict(list)
    indegree = defaultdict(int)
    
    # Build the graph and indegree count
    for index, row in df.iterrows():
        task_id = row['Id']
        if row['Predecessor']:
            for pre_id in row['Predecessor']:
                graph[pre_id].append(task_id)
                indegree[task_id] += 1
        else:
            indegree[task_id]  # Ensure tasks with no predecessors are tracked
    
    return graph, indegree

# Perform topological sort (Kahn's algorithm)
def topological_sort(graph, indegree):
    zero_indegree_queue = deque([task for task in indegree if indegree[task] == 0])
    sorted_tasks = []
    
    while zero_indegree_queue:
        task = zero_indegree_queue.popleft()
        sorted_tasks.append(task)
        
        for successor in graph[task]:
            indegree[successor] -= 1
            if indegree[successor] == 0:
                zero_indegree_queue.append(successor)
    
    return sorted_tasks


def project_total_delay(df):
    # Ensure the Predecessor column is properly formatted as a list of integers
    df['Predecessor'] = df['Predecessor'].apply(lambda x: [int(i) for i in str(x).split(',')] if x != '0' else [])
    # Build the task graph and calculate indegrees
    graph, indegree = build_graph(df)

    # Get the topologically sorted tasks
    sorted_tasks = topological_sort(graph, indegree)

    # Initialize task delays
    task_delays = {}

    # Process tasks in topological order to calculate delays
    for task_id in sorted_tasks:
        task_row = df[df['Id'] == task_id].iloc[0]
        predecessors = task_row['Predecessor']
        
        # Calculate start delay from predecessors
        if predecessors:
            # Get the maximum delay among the predecessors
            predecessor_delays = [task_delays[pre_id] for pre_id in predecessors]
            start_delay = max(predecessor_delays) if predecessor_delays else 0
        else:
            start_delay = 0
        
        # Total delay is the start delay plus the task's own prediction delay
        task_delays[task_id] = start_delay + task_row['Prediction']

    # The total project delay is the maximum delay among all tasks
    total_project_delay = max(task_delays.values())

    return total_project_delay

def calculate_shap_average(df):
    # Create a new DataFrame to store SHAP values for each feature
    shap_df = pd.json_normalize(df['SHAP_score'])

    # Calculate the mean SHAP score for each feature
    mean_shap_scores = shap_df.mean()

    return mean_shap_scores.to_dict()