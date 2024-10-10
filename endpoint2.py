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
from flask_restx import Api, reqparse, fields, Resource, Namespace

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

#Example file for predict_project_delay
with open('/src/app/data/predict_project_delay_input_example2-3.json') as f:
    json_example = json.load(f)


# Define the parser for file upload
upload_parser = reqparse.RequestParser()
upload_parser.add_argument('file', location='files', type='FileStorage', required=True, help='CSV file with task data')

api = Api(app, version="1.0", title="Method Prediction API")

ns1_route = Namespace('DelayPrediction', description='API endpoint for delay task and project delay prediction')

# Define a model schema for input data
task_model = api.model('SinglePrediction', {
    'Duration': fields.Float(required=True, description='Task expected duration (days)'),
    'Trade': fields.Float(required=True, description='Task trade category (0~35)'),
    'Progres': fields.Float(required=True, description='Task progress in percentage (%)'),
    'WorkerScore': fields.Float(requird=True, decription='Worker score assesment who handle the task (0~100)'),
    'Temperature': fields.Float(required=True, description='Average daily temperature when the task is carried out (Celcius)'),
    'RainProb': fields.Float(required=True, description='Average daily rain probability when the task is carried out (%)'),
    'WindSpeed': fields.Float(requred=True, description='Average daily wind speed when the task is carried out (Km/h)')
})

# Define the extended model for 'MultiplePrediction' with Task_Id
task_model2 = api.model('MultiplePrediction', {
    'headers': fields.List(fields.String, required=True, description='Headers for task attributes', example=[
        "Task_Id", 
        "Duration", 
        "Trade", 
        "Progress", 
        "WorkerScore", 
        "Temperature", 
        "RainProb", 
        "WindSpeed"
    ]),
    'values': fields.List(fields.List(fields.Float), required=True, description="List of task values", example=[
        [
            1,
            3,
            32,
            70,
            1,
            21,
            0,
            5
        ],
        [
            2,
            1,
            27,
            50,
            1,
            25,
            50,
            15
        ],
        [
            3,
            2,
            20,
            95,
            1,
            19,
            0,
            10
        ]
    ])
})

# Define the model for ProjectTasks with Task_Id and relevant fields
task_model3 = api.model('ProjectTasksModel', { 
    'header': fields.List(fields.String, required=True, description="Headers for task attributes", example=[
        "Task_Id",
        "Predecessor",
        "Successor",
        "Duration",
        "Trade",
        "Progress",
        "WorkerScore",
        "Temperature",
        "RainProb",
        "WindSpeed"
    ]),
    'values': fields.List(fields.List(fields.Raw), required=True, description="Values for the tasks", example=json_example['values'])
})

#predict single task endpoint
@ns1_route.route('/predict_single_task')
class PredictSingleTask(Resource):
    @ns1_route.expect(task_model)
    @ns1_route.response(200, 'Success', fields.String(description='Prediction value'))
    @ns1_route.response(400, 'Invalid Input', fields.String(description='Error message'))
    @ns1_route.doc(description="Make a prediction for a single task based on the provided features.")
    def post(self):
        """Predict single task based on input features"""
        try:
            data = request.json
            data_df = pd.DataFrame([data])

            # Prediction
            prediction = model.predict(data_df)  # Replace with actual model prediction
            if prediction[0] < 1:
                prediction[0] = 0.0

            result = {
                'prediction': float(prediction[0])
            }
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 400

#predict multiple task endpoint    
@ns1_route.route('/predict_multiple_task')
class PredictMultipleTasks(Resource):
    @ns1_route.expect(task_model2)
    @ns1_route.response(200, 'Success', fields.String(description='JSON object with predictions and SHAP values'))
    @ns1_route.response(400, 'Invalid Input', fields.String(description='Error message'))
    @ns1_route.response(500, 'Internal Server Error', fields.String(description='Error message'))
    def post(self):
        """Predict multiple tasks based on JSON input, and return the results as JSON"""
        try:
            # Parse JSON input
            data = request.json
            headers = data.get('headers', [])
            values = data.get('values', [])

            # If headers or values are missing
            if not headers or not values:
                return jsonify({'error': 'Headers or values missing from input'}), 400

            # Convert the JSON input to a DataFrame
            data_df = pd.DataFrame(values, columns=headers)

            # Separate 'Task_Id' from the data for prediction
            task_ids = data_df['Task_Id']
            data_df = data_df.drop(columns=['Task_Id'])

            # Ensure required columns are present for prediction
            required_columns = required_column_task()

            if not all(col in data_df.columns for col in required_columns):
                return jsonify({'error': f'Missing required columns. Required columns are: {required_columns}'}), 400

            # Ensure columns are in the correct order
            data_df = data_df[required_columns]

            # Prepare background data
            background_df = pd.DataFrame(background_data, index=[0])
            background_df = background_df.drop(columns=['Unnamed: 0'], axis=1)

            # ML Model
            # shap_eval = SHAP_Evaluation(model, data_df, background_df, model_code='ML')

            # Neural Network Model
            shap_eval = SHAP_Evaluation(model, data_df, background_df, model_code='DL')

            # Ensemble Model
            # shap_eval = SHAP_Evaluation(model, data_df, background_df, model_code='EL')

            shap_dicts = shap_eval.SHAP_Dictionary()

            # Prediction
            predictions = model.predict(data_df)

            # Apply the conditions to round and set the predictions
            rounded_predictions = np.where(predictions < 0.5, 0, np.where(predictions % 1 >= 0.5, np.ceil(predictions), np.floor(predictions)).astype(int))

            # Apply a minimum of 1 for any predictions between 0.5 and 1
            rounded_predictions = np.where((rounded_predictions > 0) & (rounded_predictions < 1), 1, rounded_predictions)

            # Build the response payload with Task_Id, Prediction, and SHAP_Score
            response_payload = []
            for idx, task_id in enumerate(task_ids):
                response_payload.append({
                    "Task_Id": int(task_id),
                    "Prediction": int(rounded_predictions[idx]),
                    "SHAP_Score": {key: shap_dicts[idx][key] for key in required_columns}
                })

            # Return as JSON response
            return jsonify(response_payload)
        except Exception as e:
            print(traceback.format_exc())
            return jsonify({'error': str(e)}), 500
    

#Predict project delay endpoint
@ns1_route.route('/predict_project_delay')
class PredictProjectDelay(Resource):
    @ns1_route.expect(task_model3)
    @ns1_route.response(200, 'Success', fields.String(description='Project delay prediction payload'))
    @ns1_route.response(400, 'Invalid Input', fields.String(description='Error message'))
    @ns1_route.response(500, 'Internal Server Error', fields.String(description='Error message'))
    @ns1_route.doc(description="Upload a JSON object with project tasks to predict the total project delay.")
    def post(self):
        """Predict the whole project total delay"""
        try:
            # Parse JSON input
            data = request.json
            headers = data.get('header', [])
            values = data.get('values', [])

            # If headers or values are missing
            if not headers or not values:
                return jsonify({'error': 'Headers or values missing from input'}), 400

            # Convert the values to a DataFrame using the headers
            data_df = pd.DataFrame(values, columns=headers)

            # Ensure required columns are present
            required_columns = required_column_project()

            if not all(col in data_df.columns for col in required_columns):
                return jsonify({'error': f'Missing required columns. Required columns are: {required_columns}'}), 400

            # Ensure columns are in the correct order
            data_df = data_df[required_columns]

            # Process the relevant columns
            partial_df = data_df.iloc[:, 3:]

            # Prepare background data
            background_df = pd.DataFrame(background_data, index=[0])
            background_df = background_df.drop(columns=['Unnamed: 0'], axis=1)

            # Neural Network Model
            shap_eval = SHAP_Evaluation(model, partial_df, background_df, model_code='DL')

            shap_dicts = shap_eval.SHAP_Dictionary()

            # Add predictions to the DataFrame
            predictions = model.predict(partial_df)
            rounded_predictions = np.where(predictions < 0.5, 0, np.where(predictions % 1 >= 0.5, np.ceil(predictions), np.floor(predictions)).astype(int))
            rounded_predictions_list = [pred[0] if isinstance(pred, list) else pred for pred in rounded_predictions.tolist()]
            data_df['Prediction'] = rounded_predictions_list

            # Add SHAP scores to the DataFrame
            data_df['SHAP_score'] = shap_dicts

            # Convert shap_dicts (list of dicts) to JSON-serializable format
            shap_dicts_serializable = []
            for shap_dict in shap_dicts:
                shap_dict_serialized = {key: float(value) for key, value in shap_dict.items()}
                shap_dicts_serializable.append(shap_dict_serialized)

            # Calculate total project delay
            sequential_delay = project_total_delay(data_df)

            # Average SHAP scores
            average_shap = calculate_shap_average(data_df)

            # Prepare predicted task details
            predicted_task_details = []
            for idx, row in data_df.iterrows():
                predicted_task_details.append({
                    "Task_id": int(row["Task_Id"]),
                    "Prediction": int(rounded_predictions_list[idx]),
                    "SHAP_Score": shap_dicts_serializable[idx]
                })

            # Create the final response payload
            payload = {
                "project_delay": int(sequential_delay),
                "average_shap": average_shap,
                "predicted_task_details": predicted_task_details
            }

            # Return the payload as a JSON response
            return jsonify(payload)
        except Exception as e:
            print(traceback.format_exc())
            return jsonify({'error': str(e)}), 500
        
#Feature Importance endpooint
@ns1_route.route('/feature_importance')
class FeatureImportance(Resource):
    @ns1_route.expect(task_model)
    @ns1_route.response(200, 'Success', fields.Raw(description='SHAP feature importance values'))
    @ns1_route.response(500, 'Internal Server Error', fields.String(description='Error message'))
    @ns1_route.doc(description="Get feature importance using SHAP values based on input features.")
    def post(self):
        """Get feature importance from single task prediction"""
        try:
            # Parse the input data
            data = request.json
            data_df = pd.DataFrame(data, index=[0])
            background_df = pd.DataFrame(background_data, index=[0])

            # Drop unnecessary columns
            background_df = background_df.drop(columns=['Unnamed: 0'], axis=1)

            # ML Model
            # shap_eval = SHAP_Evaluation(model, data_df, background_df, model_code='ML')

            # Neural Network Model
            shap_eval = SHAP_Evaluation(model, data_df, background_df, model_code='DL')

            # Ensemble Model
            # shap_eval = SHAP_Evaluation(model, data_df, background_df, model_code='EL')

            # Calculate SHAP values
            # shap_values = shap_eval.SHAP_Calculation()

            # Plot the SHAP values
            # shap.summary_plot(shap_values, data_df, plot_type="bar", feature_names=data_df.columns, show=False)
            # plt.savefig("feature_importance.png")
            # plt.close()

            # Return the SHAP dictionary
            shap_dicts = shap_eval.SHAP_Dictionary()

            return shap_dicts
        except Exception as e:
            print(traceback.format_exc())
            return jsonify({'error': str(e)}), 500
        
#Header namespacec
api.add_namespace(ns1_route)
    
if __name__ == '__main__':
    # Default port is 5500 if no port argument is provided
    port = 5500
    if len(sys.argv) > 1 and sys.argv[1] == '--port':
        port = int(sys.argv[2])  # Use the port passed in the command-line argument
    app.run(host="0.0.0.0", port=port, debug=True)