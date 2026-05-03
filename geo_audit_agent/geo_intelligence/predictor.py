import pandas as pd
import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import os
import numpy as np

def build_training_data():
    if os.path.exists('data/training_data.csv'):
        return pd.read_csv('data/training_data.csv')
    return pd.DataFrame()

def train_model():
    df = build_training_data()
    if df.empty:
        print("Error: No training data found.")
        return None
    
    features = ['has_json_ld', 'has_technical_whitepaper', 'has_reviews', 
                'competition_level', 'brand_age_months', 'backlink_count', 'semantic_score']
    X = df[features]
    y = df['confidence_score']
    
    mlflow.set_experiment("GEO_Potential_Score")
    
    with mlflow.start_run():
        mlflow.sklearn.autolog()
        
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)
        
        predictions = model.predict(X)
        r2 = r2_score(y, predictions)
        mae = mean_absolute_error(y, predictions)
        # Fix for squared parameter in scikit-learn >= 1.4 (or use np.sqrt)
        mse = mean_squared_error(y, predictions)
        rmse = np.sqrt(mse)
        
        print(f"Model Performance:")
        print(f"R-squared: {r2:.4f}")
        print(f"MAE: {mae:.4f}")
        print(f"RMSE: {rmse:.4f}")
        
        mlflow.log_metric("r2_score", r2)
        mlflow.log_metric("mae", mae)
        mlflow.log_metric("rmse", rmse)
        
        mlflow.sklearn.log_model(
            sk_model=model,
            artifact_path="geo-model",
            registered_model_name="GEO_Potential_Predictor"
        )
        
        client = mlflow.tracking.MlflowClient()
        versions = client.get_latest_versions("GEO_Potential_Predictor")
        latest_version = versions[0].version if versions else "1"
        client.set_registered_model_tag("GEO_Potential_Predictor", "production", "true")
        print(f"Model registered as version {latest_version} with tag 'production'")
            
        return model, latest_version

def predict_score(features_dict):
    features_list = ['has_json_ld', 'has_technical_whitepaper', 'has_reviews', 
                    'competition_level', 'brand_age_months', 'backlink_count', 'semantic_score']
    
    df = build_training_data()
    if df.empty:
        return 0.0
        
    X = df[features_list]
    y = df['confidence_score']
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    
    input_df = pd.DataFrame([features_dict])[features_list]
    prediction = model.predict(input_df)[0]
    return min(max(prediction * 100, 0), 100)
