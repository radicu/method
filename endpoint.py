from flask import Flask, request, jsonify
import pandas as pd
import h2o
from h2o.automl import H2OAutoML
h2o.init()

app = Flask(__name__)

model = h2o.load_model("model/30_2018_30")

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    data_df = pd.DataFrame(data, index=[0])
    data_h2o = h2o.H2OFrame(data_df)
    prediction = model.predict(data_h2o)
    result = {
        'prediction' : prediction.as_data_frame().iat[0, 0]
    }
    
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)