import sys
import h2o
from h2o.automl import H2OAutoML
import pandas as pd

class H2OModel:
    def __init__(self, df, y_target):
        self.df = df
        self.y_target = y_target
        self.hf = None
        self.data_train = None
        self.data_test = None
        self.data_valid = None
        self.x_features = None
        self.aml = None
        self.model = None
        self.mae = None
        self.shap = None

    def initialize(self):
        h2o.init()
        self.hf = h2o.H2OFrame(self.df)
        self.data_train, self.data_test, self.data_valid = self.hf.split_frame(ratios=[.8, .1])

    def run_modelling(self):
        self.x_features = self.df.columns.tolist()
        self.x_features = [x for x in self.x_features if x != self.y_target]

        self.aml = H2OAutoML(max_models=10, seed=10, verbosity="info", nfolds=0)
        self.aml.train(x=self.x_features, y=self.y_target, training_frame=self.data_train, validation_frame=self.data_valid)

        self.model = self.aml.leader

    def get_model(self):
        return self.model

    def get_mae(self):
        return self.model.mae(valid=True)

    def get_shap(self):
        return self.model.shap_summary_plot(self.data_test)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python class_automl_h20.py <data_path> <target_column>")
        sys.exit(1)

    data_path = sys.argv[1]
    data_file = pd.read_csv(data_path)
    target_column = sys.argv[2] 

    model_obj = H2OModel(data_file, target_column)
    model_obj.initialize()
    model_obj.run_modelling()

    model = model_obj.get_model()
    mae = model_obj.get_mae()

    print(f"MAE: {mae}")
    model_obj.get_shap()
