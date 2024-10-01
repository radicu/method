from flask import Flask, request, send_file, jsonify
import pandas as pd
import joblib
import shap
import traceback
import matplotlib.pyplot as plt
import matplotlib
import io
import boto3
import joblib

# Use the 'Agg' backend for matplotlib
matplotlib.use('Agg')

app = Flask(__name__)

# Load the model
# model = joblib.load("./model/30_2018_30_v2.pkl")
# model = joblib.load("./model/10_2019_v2.pkl")
# model = joblib.load("./model/10_2020_v2.pkl")

# Load the model from S3
def load_model_from_s3(bucket_name, model_key):
    s3 = boto3.client('s3')
    s3.download_file(bucket_name, model_key, '/tmp/model.pkl')
    model = joblib.load('/tmp/model.pkl')
    return model

bucket_name = 'method-model-v1'
model_key = 'model/10_2019_v2.pkl'

model = load_model_from_s3(bucket_name, model_key)

@app.route('/predict_single_task', methods=['POST'])
def predict():
    try:
        data = request.json
        data_df = pd.DataFrame(data, index=[0])

        # Prediction
        prediction = model.predict(data_df)

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
        
        # Ensure required columns are present
        required_columns = [
            'Cost', 'Priority', 'Progress', 'Duration', 'Worker',
            'TaskLength', 'IsBadWeather', 'WeatherAssessment', 
            'StartDelay', 'DayCount', 'Is_Delayed'
        ]
        
        if not all(col in data_df.columns for col in required_columns):
            return jsonify({'error': f'Missing required columns. Required columns are: {required_columns}'}), 400

        # Ensure columns are in the correct order
        data_df = data_df[required_columns]

        # Debugging: Print the shape and columns of the input data
        print("Input Data Shape:", data_df.shape)
        print("Input Data Columns:", data_df.columns)

        # Calculate SHAP values
        explainer = shap.Explainer(model)
        shap_values = explainer(data_df)

        # Debugging: Print the shape of the SHAP values
        print("SHAP Values Shape:", shap_values)

        # Add SHAP values to the dataframe
        shap_dicts = []
        for row in shap_values.values:
            shap_dicts.append({col: val for col, val in zip(data_df.columns, row)})
        
        # Create a copy of data_df to avoid modifying the original DataFrame
        output_df = data_df.copy()
        output_df['SHAP_score'] = shap_dicts
        
        # Prediction
        predictions = model.predict(data_df)
        output_df['Prediction'] = predictions
        
        # Convert the dataframe to CSV
        output = io.BytesIO()
        output_df.to_csv(output, index=False)
        output.seek(0)
        
        return send_file(output, mimetype='text/csv', download_name='predictions.csv', as_attachment=True)
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/feature_importance', methods=['POST'])
def feature_importance():
    try:
        data = request.json
        data_df = pd.DataFrame(data, index=[0])

        # Calculate SHAP values
        explainer = shap.Explainer(model)
        shap_values = explainer(data_df)

        # Plot the SHAP values
        shap.summary_plot(shap_values, data_df, plot_type="bar", show=False)
        plt.savefig("feature_importance.png")
        plt.close()

        return send_file("feature_importance.png", mimetype='image/png')
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
