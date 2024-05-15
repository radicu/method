import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import mpld3
import streamlit.components.v1 as components
import os
import random
import numpy as np
from scipy import stats
from sklearn.tree import DecisionTreeRegressor
from sklearn.metrics import mean_absolute_error

def read_csv_files(directory):
    files = ['task_data.csv', 'task_train.csv', 'project_data.csv', 'project_train.csv']
    dataframes = {}
    for file in files:
        filepath = os.path.join(directory, file)
        if os.path.exists(filepath):
            dataframes[file] = pd.read_csv(filepath)
        else:
            st.warning(f"File {file} not found in directory {directory}.")
    return dataframes

def train_model(dataframes, target):
    tasks = dataframes.get('task_data.csv')
    tasks_df = dataframes.get('task_train.csv')

    if tasks is None or tasks_df is None:
        st.error("Required data files are missing.")
        return None, None, None, None

    X = tasks_df.copy()
    y = X.pop(target)

    # Split the data
    project_ids = tasks['ProjectID'].unique().tolist()
    indices = random.sample(project_ids, int(0.2 * len(project_ids)))
    val_indices = random.sample(indices, int(0.5 * len(indices)))
    test_indices = [x for x in indices if x not in val_indices]
    val_idx = tasks.loc[tasks['ProjectID'].isin(val_indices)].index.tolist()
    test_idx = tasks.loc[tasks['ProjectID'].isin(test_indices)].index.tolist()

    X_val = X[X.index.isin(val_idx)]
    y_val = y[y.index.isin(val_idx)]
    X_train = X[(~X.index.isin(test_idx)) & (~X.index.isin(val_idx))]
    y_train = y[(~y.index.isin(test_idx)) & (~y.index.isin(val_idx))]

    # Train base decision tree model
    model = DecisionTreeRegressor(max_depth=7)
    model.fit(X_train, y_train)

    y_val_pred = model.predict(X_val)
    y_train_pred = model.predict(X_train)

    mae_train = mean_absolute_error(y_train, y_train_pred)
    mae_val = mean_absolute_error(y_val, y_val_pred)
    return model, mae_train, mae_val, test_idx

def process_input(dir_name):
    data_dir = os.path.join('data', dir_name)
    if not os.path.exists(data_dir):
        st.warning("Specified directory does not exist.")
        return None
    dataframes = read_csv_files(data_dir)
    if not dataframes:
        st.warning("No data found in the specified directory.")
        return None
    return dataframes

def plot_task_progression(data):
    fig, ax = plt.subplots(figsize=(15,4))
    ax.scatter(data['Date'], data['Progress'], label='Progress', s=100)
    # ax.axvline(pd.to_datetime(data['EndDate']).iloc[0], color='blue', linestyle='--', label='Planned end date')
    if len(data['Progress'].unique())>1:
        # Fit line
        slope, intercept, r_value, p_value, std_err = stats.linregress(data.index, data['Progress'])
        line = slope * data.index + intercept
        ax.plot(data['Date'], line, color='red', label='Fit Line')

        # Error area
        residuals = data['Progress'] - (slope * data.index + intercept)
        std_residuals = np.std(residuals)
        ax.fill_between(data['Date'], line - std_residuals, line + std_residuals, color='red', alpha=0.2, label='Error Area')

        # Predict the date when progress achieves 100
        date_100 = pd.to_datetime((100 - intercept) / slope, unit='D', origin=data['Date'].min())
        ax.axvline(date_100, color='green', linestyle='--', label='Expected end date')
        st.write(f'Task is expected to be completed at **{date_100.date()}**')

    ax.axhline(100, color='black', linestyle='-', label='Complete')
    ax.axhline(0, color='black', linestyle='-')
    ax.set_xlabel('Date')
    ax.set_ylabel('Progress')
    ax.set_title('Progress Over Time')
    ax.legend()
    return fig

def plot_project_progression(data):
    fig, ax = plt.subplots(figsize=(15,4))
    ax.scatter(data['Date'], data['Progress'], label='Progress', s=10)
    # ax.axvline(pd.to_datetime(data['EndDate']).iloc[0], color='blue', linestyle='--', label='Planned end date')
    if len(data['Progress'].unique())>1:
        # Fit line
        slope, intercept, r_value, p_value, std_err = stats.linregress(data.index, data['Progress'])
        line = slope * data.index + intercept
        ax.plot(data['Date'], line, color='red', label='Fit Line')

        # Error area
        residuals = data['Progress'] - (slope * data.index + intercept)
        std_residuals = np.std(residuals)
        ax.fill_between(data['Date'], line - std_residuals, line + std_residuals, color='red', alpha=0.2, label='Error Area')

        # Predict the date when progress achieves 100
        date_100 = pd.to_datetime((100 - intercept) / slope, unit='D', origin=data['Date'].min())
        ax.axvline(date_100, color='green', linestyle='--', label='Expected end date')
        st.write(f'Project is expected to be completed at **{date_100.date()}**')

    ax.axhline(100, color='black', linestyle='-', label='Complete')
    ax.axhline(0, color='black', linestyle='-')
    ax.set_xlabel('Date')
    ax.set_ylabel('Progress')
    ax.set_title('Progress Over Time')
    ax.legend()
    return fig
    
def display(data):
    with st.expander("About the Model"):
        st.write(f"Model Type : Decision Tree Regressor")
        st.write(f"**Train MAE: {data['mae_train']:.2f} | Validation MAE: {data['mae_val']:.2f}**")
    
    test_tasks = data['test_data']
    test_tasks['Date'] = pd.to_datetime(test_tasks['Date']).dt.date
    test_projects = data['dataframes']['project_data.csv']
    test_projects['Date'] = pd.to_datetime(test_projects['Date']).dt.date
    pred_data = data['pred_data']
    test_tasks_pids = test_tasks['ProjectID'].unique()
    
    if len(test_tasks_pids) > 0:
        test_pid_select = st.sidebar.selectbox('Test Project ID :', test_tasks_pids, help='select project ID from the test set')
        test_tasks_select_data = test_tasks[test_tasks['ProjectID'] == test_pid_select]
        
        with st.expander("About the Project"):
            st.write(f"Project ID : **{test_pid_select}**")
            st.write(f"Number of tasks : **{test_tasks_select_data['ID'].nunique()}**")
            st.write(f"Workday : **{test_tasks_select_data['WorkDay'].mean()}**")
            st.write(f"Project Start Date : **{test_tasks_select_data['ActualStartDate'].min()}**")
            st.write(f"Project End Date : **{test_tasks_select_data['ActualEndDate'].max()}**")
        
        available_dates = test_tasks_select_data['Date']
        selected_date = st.sidebar.date_input("Select Date", value=available_dates.min(), min_value=available_dates.min(), max_value=available_dates.max(), help='select a date from available dates in the project')
            
        st.sidebar.info(f'Valid date range is from {available_dates.min()} to {available_dates.max()}')
        test_tasks_select_data_filtered = test_tasks_select_data[test_tasks_select_data['Date'] == selected_date]
        test_tasks_ids = test_tasks_select_data_filtered['ID'].unique().tolist()
        test_tasks_select = st.sidebar.selectbox('Test Tasks ID :', test_tasks_ids, help='select task ID from the project')
        task_select_data = test_tasks_select_data[(test_tasks_select_data['ID'] == test_tasks_select) & (test_tasks_select_data['Date'] <= selected_date)].reset_index(drop=False)
        
        st.write(f"### Current date : {selected_date}")
        test_projects_select_data = test_projects[(test_projects['ProjectID'] == test_pid_select) & (test_projects['Date']<= selected_date)].reset_index(drop=True)
        fig_project = plot_project_progression(test_projects_select_data)
        st.pyplot(fig_project)
        
        data_last_index = task_select_data.iloc[-1]['index']
        data_last = pred_data.iloc[data_last_index]
        data_ground_truth = data_last['TaskDelay']
        data_last = data_last.drop('TaskDelay')
        data_last_pred = data['model'].predict(data_last.to_numpy().reshape(1, -1))
        st.write(f'The selected tasks is estimated to be delayed for **{data_last_pred[0]:.2f} days**, true delay is **{data_ground_truth} days**')
        
        fig_task = plot_task_progression(task_select_data)
        st.pyplot(fig_task)
    else:
        st.warning("No test data available.")

def main():
    st.title("AI Delay Prediction")
    st.sidebar.title("Source Data")

    if 'results' not in st.session_state:
        st.session_state.results = {}
    
    dir_name = st.sidebar.text_input("Enter directory name:")
    
    if dir_name and dir_name not in st.session_state.results:
        dataframes = process_input(dir_name)
        if dataframes:
            st.write("Training model...")
            model, mae_train, mae_val, test_idx = train_model(dataframes, 'TaskDelay')
            if model is not None:
                st.write("Model training complete!")
                test_data = dataframes['task_data.csv'][dataframes['task_data.csv'].index.isin(test_idx)].reset_index(drop=True)
                pred_data = dataframes['task_train.csv'][dataframes['task_train.csv'].index.isin(test_idx)].reset_index(drop=True)
                st.session_state.results[dir_name] = {
                    'model' : model,
                    'dataframes' : dataframes,
                    'mae_train' : mae_train,
                    'mae_val' : mae_val,
                    'test_data' : test_data,
                    'pred_data' : pred_data
                }
        else:
            st.error("Error processing input data.")
    
    if dir_name in st.session_state.results:
        data = st.session_state.results[dir_name]
        display(data)

if __name__ == "__main__":
    main()
