import pandas as pd
import numpy as np
import keras_tuner as kt
import shap
import joblib
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Conv1D, Flatten, LSTM, MaxPooling1D, Dropout, RepeatVector, BatchNormalization
from tensorflow.keras.optimizers import Adam, RMSprop
from tensorflow.keras.regularizers import l2
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.model_selection import train_test_split, KFold
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import LabelEncoder

# Load dataset
df2 = pd.read_excel("./data/New_Dummy/Project Dummy Data.xlsx", sheet_name="Task_Table1") 

# Data preprocessing function
def preprocess_project(df):
    df['StartDate'] = pd.to_datetime(df['StartDate'])
    df['EndDate'] = pd.to_datetime(df['EndDate'])
    df['ActualStartDate'] = pd.to_datetime(df['ActualStartDate'])
    df['ActualEndDate'] = pd.to_datetime(df['ActualEndDate'])
    df['Trade'] = LabelEncoder().fit_transform(df['Trade'])
    return df

# CNN-LSTM model with Batch Normalization, Dropout, L2 regularization
def build_model(hp, input_shape):
    model = Sequential()

    # CNN part
    model.add(Conv1D(
        filters=hp.Int('filters_1', min_value=32, max_value=256, step=32),
        kernel_size=hp.Int('kernel_size_1', min_value=2, max_value=5, step=1),
        activation='relu',
        input_shape=(input_shape, 1),
        padding='same',
        kernel_regularizer=l2(1e-4)
    ))
    model.add(BatchNormalization())
    model.add(MaxPooling1D(pool_size=2))

    model.add(Conv1D(
        filters=hp.Int('filters_2', min_value=32, max_value=256, step=32),
        kernel_size=hp.Int('kernel_size_2', min_value=2, max_value=5, step=1),
        activation='relu',
        padding='same',
        kernel_regularizer=l2(1e-4)
    ))
    model.add(BatchNormalization())
    model.add(Flatten())

    # LSTM part
    model.add(RepeatVector(input_shape))
    model.add(LSTM(
        units=hp.Int('lstm_units_1', min_value=32, max_value=256, step=32),
        return_sequences=True,
        kernel_regularizer=l2(1e-4)
    ))
    model.add(LSTM(
        units=hp.Int('lstm_units_2', min_value=32, max_value=256, step=32),
        return_sequences=False,
        kernel_regularizer=l2(1e-4)
    ))
    model.add(BatchNormalization())

    # Dropout layer for regularization
    model.add(Dropout(rate=hp.Float('dropout_rate', min_value=0.0, max_value=0.5, step=0.1)))

    # Output layer
    model.add(Dense(1, kernel_regularizer=l2(1e-4)))

    # Compile the model with a tunable optimizer
    model.compile(
        optimizer=RMSprop(learning_rate=hp.Float('learning_rate', min_value=1e-4, max_value=1e-2, sampling='LOG')),
        loss='mean_absolute_error'
    )
    
    return model

# Hyperparameter tuning function
def tune_model(X_train, y_train, X_val, y_val, input_shape):
    tuner = kt.RandomSearch(
        lambda hp: build_model(hp, input_shape=input_shape),
        objective='val_loss',
        max_trials=20,  # Increased number of trials for broader search
        executions_per_trial=3,
        directory='tuning_dir',
        project_name='cnn_lstm_extended_tuning'
    )
    tuner.search(X_train, y_train, epochs=50, validation_data=(X_val, y_val), verbose=1)
    
    # Get the best hyperparameters
    best_hps = tuner.get_best_hyperparameters(num_trials=1)[0]
    best_model = tuner.hypermodel.build(best_hps)

    return best_model

# Train and evaluate the model with cross-validation
def train_evaluate_model(df, target, background_data):
    X = df.drop(columns=[target])
    y = df[target]
    X = np.expand_dims(X.values, axis=2)
    
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    mae_scores = []
    rmse_scores = []
    r2_scores = []
    
    # Perform cross-validation
    for train_index, val_index in kf.split(X):
        X_train, X_val = X[train_index], X[val_index]
        y_train, y_val = y[train_index], y[val_index]
        input_shape = X_train.shape[1]

        # Tune and train the model
        best_model = tune_model(X_train, y_train, X_val, y_val, input_shape)

        # Early stopping
        early_stopping = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
        history = best_model.fit(X_train, y_train, validation_data=(X_val, y_val), 
                                 epochs=100, batch_size=20, verbose=1, callbacks=[early_stopping])

        # Make predictions
        y_val_pred = best_model.predict(X_val)
        y_train_pred = best_model.predict(X_train)

        mae_train = mean_absolute_error(y_train, y_train_pred)
        mae_val = mean_absolute_error(y_val, y_val_pred)
        rmse_val = np.sqrt(mean_squared_error(y_val, y_val_pred))
        r2_val = r2_score(y_val, y_val_pred)

        # Append scores
        mae_scores.append(mae_val)
        rmse_scores.append(rmse_val)
        r2_scores.append(r2_val)

        print(f"MAE Train: {mae_train}, MAE Validation: {mae_val}")
        print(f"RMSE Validation: {rmse_val}, R² Validation: {r2_val}")

    # Average cross-validation scores
    avg_mae = np.mean(mae_scores)
    avg_rmse = np.mean(rmse_scores)
    avg_r2 = np.mean(r2_scores)

    print(f"\nAverage MAE: {avg_mae}")
    print(f"Average RMSE: {avg_rmse}")
    print(f"Average R²: {avg_r2}")

    return best_model

# Preprocess the dataset
processed_df = preprocess_project(df2)
train_df = processed_df.drop(columns=['ID', 'Outline_Number','Name','StartDate','EndDate', 'Predecessors', 'Successors', 'ActualStartDate','ActualEndDate'])

# Prepare background data for SHAP
background_data = train_df.drop(columns=['Delay']).sample(n=100, random_state=42)

# Train and evaluate the model with cross-validation
best_model = train_evaluate_model(train_df, 'Delay', background_data)

# Save the final model
joblib.dump(best_model, './model/30_2019_v6_CNN_LSTM_Final_Tuned.pkl')
