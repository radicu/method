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

# Define the parser for file upload
upload_parser = reqparse.RequestParser()
upload_parser.add_argument('file', location='files', type='FileStorage', required=True, help='CSV file with task data')

api = Api(app, version="1.0", title="Method Prediction API")

ns1_route = Namespace('DelayPrediction', description='API endpoint for delay task and project delay prediction')

# Define a model schema for input data
task_model = api.model('TaskModel', {
    'Duration': fields.Float(required=True, description='Task expected duration (days)'),
    'Trade': fields.Float(required=True, description='Task trade category (0~35)'),
    'Progres': fields.Float(required=True, description='Task progress in percentage (%)'),
    'WorkerScore': fields.Float(requird=True, decription='Worker score assesment who handle the task (0~100)'),
    'Temperature': fields.Float(required=True, description='Average daily temperature when the task is carried out (Celcius)'),
    'RainProbability': fields.Float(required=True, description='Average daily rain probability when the task is carried out (%)'),
    'WindSpeed': fields.Float(requred=True, description='Average daily wind speed when the task is carried out (Km/h)')
})

# Load the model
# model = joblib.load("./model/LSTM_V7.pkl")
model = joblib.load("/src/app/model/LSTM_V7.pkl")

# background data
# background_data = pd.read_csv("./data/background_data.csv")
background_data = pd.read_csv("/src/app/data/background_data.csv")


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
    @ns1_route.expect(upload_parser)
    @ns1_route.response(200, 'Success', fields.String(description='CSV file with predictions'))
    @ns1_route.response(400, 'Invalid Input', fields.String(description='Error message'))
    @ns1_route.response(500, 'Internal Server Error', fields.String(description='Error message'))
    def post(self):
        """Predict multiple tasks based on CSV input"""
        try:
            # File parsing
            file = request.files['file']
            if not file:
                return jsonify({'error': 'No file provided'}), 400

            # Read CSV file into DataFrame
            data_df = pd.read_csv(file)

            # Debugging: Print the DataFrame columns to check for discrepancies
            # print("DataFrame Columns:", data_df.columns.tolist())

            # Ensure required columns are present
            required_columns = required_column_task()

            if not all(col in data_df.columns for col in required_columns):
                return jsonify({'error': f'Missing required columns. Required columns are: {required_columns}'}), 400

            # Ensure columns are in the correct order
            data_df = data_df[required_columns]

            # Prepare background data
            background_df = pd.DataFrame(background_data, index=[0])
            background_df = background_df.drop(columns=['Unnamed: 0'], axis=1)

            # Debugging: Print the shape and columns of the input data
            # print("Input Data Shape:", data_df.shape)
            # print("Input Data Columns:", data_df.columns)

            # ML Model
            # shap_eval = SHAP_Evaluation(model, data_df, background_df, model_code='ML')

            # Neural Network Model
            shap_eval = SHAP_Evaluation(model, data_df, background_df, model_code='DL')

            # Ensemble Model
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

            # Send file response
            return send_file(output, mimetype='text/csv', download_name='predictions.csv', as_attachment=True)
        except Exception as e:
            print(traceback.format_exc())
            return jsonify({'error': str(e)}), 500
    

#Predict project delay endpoint
@ns1_route.route('/predict_project_delay')
class PredictProjectDelay(Resource):
    @ns1_route.expect(upload_parser)
    @ns1_route.response(200, 'Success', fields.String(description='Project delay prediction payload'))
    @ns1_route.response(400, 'Invalid Input', fields.String(description='Error message'))
    @ns1_route.response(500, 'Internal Server Error', fields.String(description='Error message'))
    @ns1_route.doc(description="Upload a CSV file with project tasks to predict the total project delay.")
    def post(self):
        """Predict the whole project total delay"""
        try:
            # File parsing
            file = request.files['file']
            if not file:
                return jsonify({'error': 'No file provided'}), 400
            
            # Read CSV file into DataFrame
            data_df = pd.read_csv(file)

            # Debugging: Print the DataFrame columns to check for discrepancies
            # print("DataFrame Columns:", data_df.columns.tolist())

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

            # ML Model
            # shap_eval = SHAP_Evaluation(model, partial_df, background_df, model_code='ML')

            # Neural Network Model
            shap_eval = SHAP_Evaluation(model, partial_df, background_df, model_code='DL')

            # Ensemble Model
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

            # Calculate total project delay
            sequential_delay = project_total_delay(output_df)

            # Average SHAP payload
            payload = {
                'project_delay': int(sequential_delay),
                'average_shap': calculate_shap_average(output_df)
            }

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