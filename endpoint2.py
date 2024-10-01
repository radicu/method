from flask import Flask, request, send_file, jsonify
import pandas as pd
import joblib
import shap
import traceback
import matplotlib.pyplot as plt
import matplotlib
import io
import numpy as np
import sys
import json

from utility import *

# Use the 'Agg' backend for matplotlib
matplotlib.use('Agg')

app = Flask(__name__)


# Load the model
# model = joblib.load("./model/LSTM_V7.pkl")
model = joblib.load("/src/app/model/LSTM_V7.pkl")

# background data
# background_data = pd.read_csv("./data/background_data.csv")
background_data = pd.read_csv("/src/app/data/background_data.csv")



@app.route('/predict_single_task', methods=['POST'])
def predict():
    try:
        data = request.json
        data_df = pd.DataFrame(data, index=[0])

        # Prediction
        prediction = model.predict(data_df)

        if prediction[0] < 1:
            prediction[0] = 0.0

        result = {
            'prediction': float(prediction[0])
        }
        
        return jsonify(result)
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500
    
@app.route('/predict_multiple_task', methods=['POST'])
def predict_multiple_tasks():
    try:
        file = request.files['file']
        if not file:
            return jsonify({'error': 'No file provided'}), 400
        
        data_df = pd.read_csv(file)

        # Debugging: Print the DataFrame columns to check for discrepancies
        # print("DataFrame Columns:", data_df.columns.tolist())

        # Ensure required columns are present
        required_columns = required_column_task()
        
        if not all(col in data_df.columns for col in required_columns):
            return jsonify({'error': f'Missing required columns. Required columns are: {required_columns}'}), 400

        # Ensure columns are in the correct order
        data_df = data_df[required_columns]

        background_df = pd.DataFrame(background_data, index=[0])

        background_df = background_df.drop(columns=['Unnamed: 0'], axis=1)

        # Debugging: Print the shape and columns of the input data
        # print("Input Data Shape:", data_df.shape)
        # print("Input Data Columns:", data_df.columns)

        # ML Model
        # shap_eval = SHAP_Evaluation(model, data_df, background_df, model_code='ML')

        # Neural Network Model
        shap_eval = SHAP_Evaluation(model, data_df, background_df, model_code='DL')

        #Ensemble Model
        # shap_eval = SHAP_Evaluation(model, data_df, background_df, model_code='EL')

        shap_dicts = shap_eval.SHAP_Dictionary()
        
        # Create a copy of data_df to avoid modifying the original DataFrame
        output_df = data_df.copy()
        output_df['SHAP_score'] = shap_dicts
        
        # Prediction
        predictions = model.predict(data_df)

        # Apply the conditions to round and set the predictions
        rounded_predictions = np.where(predictions < 0.5, 0, np.where(predictions % 1 >= 0.5, np.ceil(predictions), np.floor(predictions)).astype(int))

        # Apply a minimum of 1 for any predictions between 0.5 and 1
        rounded_predictions = np.where((rounded_predictions > 0) & (rounded_predictions < 1), 1, rounded_predictions)

        output_df['Prediction'] = rounded_predictions
        
        # Convert the dataframe to CSV
        output = io.BytesIO()
        output_df.to_csv(output, index=False)
        output.seek(0)
        
        return send_file(output, mimetype='text/csv', download_name='predictions.csv', as_attachment=True)
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500
    

@app.route('/predict_project_delay', methods=['POST'])
def predict_project_delay():
    try:
        file = request.files['file']
        if not file:
            return jsonify({'error': 'No file provided'}), 400
        
        data_df = pd.read_csv(file)

        # Debugging: Print the DataFrame columns to check for discrepancies
        # print("DataFrame Columns:", data_df.columns.tolist())

        # Ensure required columns are present
        required_columns = reuquired_column_project()

        
        if not all(col in data_df.columns for col in required_columns):
            return jsonify({'error': f'Missing required columns. Required columns are: {required_columns}'}), 400

        # Ensure columns are in the correct order
        data_df = data_df[required_columns]

        partial_df = data_df.iloc[:, 3:]

        background_df = pd.DataFrame(background_data, index=[0])

        background_df = background_df.drop(columns=['Unnamed: 0'], axis=1)

        # ML Model
        # shap_eval = SHAP_Evaluation(model, partial_df, background_df, model_code='ML')

        # Neural Network Model
        shap_eval = SHAP_Evaluation(model, partial_df, background_df, model_code='DL')

        #Ensemble Model
        # shap_eval = SHAP_Evaluation(model, partial_df, background_df, model_code='EL')

        shap_dicts = shap_eval.SHAP_Dictionary()

        
        # Create a copy of data_df to avoid modifying the original DataFrame
        output_df = data_df.copy()
        output_df['SHAP_score'] = shap_dicts
        
        # Prediction
        predictions = model.predict(partial_df)

        # Apply the conditions to round and set the predictions
        rounded_predictions = np.where(predictions < 0.5, 0, np.where(predictions % 1 >= 0.5, np.ceil(predictions), np.floor(predictions)).astype(int))

        # Apply a minimum of 1 for any predictions between 0.5 and 1
        rounded_predictions = np.where((rounded_predictions > 0) & (rounded_predictions < 1), 1, rounded_predictions)

        output_df['Prediction'] = rounded_predictions

        sequential_delay = project_total_delay(output_df)

        # Average_shap paylaod
        payload = {
            'project_delay': int(sequential_delay),
            'average_shap': calculate_shap_average(output_df)
        }

        return jsonify(payload)
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/feature_importance', methods=['POST'])
def feature_importance():
    try:
        data = request.json
        data_df = pd.DataFrame(data, index=[0])
        background_df = pd.DataFrame(background_data, index=[0])

        background_df = background_df.drop(columns=['Unnamed: 0'], axis=1)

        # ML Model
        # shap_eval = SHAP_Evaluation(model, data_df, background_df, model_code='ML')

        # Neural Network Model
        shap_eval = SHAP_Evaluation(model, data_df, background_df, model_code='DL')

        #Ensemble Model
        # shap_eval = SHAP_Evaluation(model, data_df, background_df, model_code='EL')

        # shap_values = shap_eval.SHAP_Calculation()

        # Plot the SHAP values
        # shap.summary_plot(shap_values, data_df, plot_type="bar", feature_names=data_df.columns, show=False)
        # plt.savefig("feature_importance.png")
        # plt.close()

        # return send_file("feature_importance.png", mimetype='image/png')

        shap_dicts = shap_eval.SHAP_Dictionary()

        return shap_dicts

    except Exception as e:
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500
    
if __name__ == '__main__':
    # Default port is 5500 if no port argument is provided
    port = 5500
    if len(sys.argv) > 1 and sys.argv[1] == '--port':
        port = int(sys.argv[2])  # Use the port passed in the command-line argument
    app.run(host="0.0.0.0", port=port, debug=True)