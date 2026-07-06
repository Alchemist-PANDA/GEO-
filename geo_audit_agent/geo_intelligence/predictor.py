import logging
import os

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

try:
    import mlflow
    import mlflow.sklearn
    HAS_MLFLOW = True
except ImportError:
    HAS_MLFLOW = False

try:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

def build_training_data():
    if os.path.exists('data/training_data.csv'):
        return pd.read_csv('data/training_data.csv')
    return pd.DataFrame()

def train_model():
    df = build_training_data()
    if df.empty:
        logger.error("No training data found.")
        return None

    features = ['has_json_ld', 'has_technical_whitepaper', 'has_reviews',
                'competition_level', 'brand_age_months', 'backlink_count', 'semantic_score']
    X = df[features]
    y = df['confidence_score']

    if not HAS_SKLEARN:
        logger.warning("scikit-learn is not installed. Mocking model training.")
        return None, "1"

    if HAS_MLFLOW:
        try:
            mlflow.set_experiment("GEO_Potential_Score")
            with mlflow.start_run():
                mlflow.sklearn.autolog()

                model = RandomForestRegressor(n_estimators=100, random_state=42)
                model.fit(X, y)

                predictions = model.predict(X)
                r2 = r2_score(y, predictions)
                mae = mean_absolute_error(y, predictions)
                mse = mean_squared_error(y, predictions)
                rmse = np.sqrt(mse)

                logger.info("Model Performance: R²=%.4f MAE=%.4f RMSE=%.4f", r2, mae, rmse)

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
                logger.info("Model registered as version %s with tag 'production'", latest_version)

                return model, latest_version
        except Exception as e:
            logger.warning("MLflow tracked training failed: %s. Falling back to untracked local training.", e)

    # Local training fallback without MLflow
    try:
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)
        predictions = model.predict(X)
        r2 = r2_score(y, predictions)
        logger.info("Local Model Performance (No MLflow): R²=%.4f", r2)
        return model, "1"
    except Exception as e:
        logger.error("Error during local training fallback: %s", e)
        return None, "1"

def predict_score(features_dict):
    features_list = ['has_json_ld', 'has_technical_whitepaper', 'has_reviews',
                    'competition_level', 'brand_age_months', 'backlink_count', 'semantic_score']

    if not HAS_SKLEARN:
        # Fallback rule-based score calculation
        score = 50.0
        if features_dict.get('has_json_ld'):
            score += 10.0
        if features_dict.get('has_technical_whitepaper'):
            score += 10.0
        if features_dict.get('has_reviews'):
            score += 10.0

        semantic = float(features_dict.get('semantic_score', 0.5))
        score += (semantic - 0.5) * 30.0

        comp = float(features_dict.get('competition_level', 0.5))
        score -= (comp - 0.5) * 10.0

        backlinks = float(features_dict.get('backlink_count', 0.0))
        if backlinks > 0:
            import math
            score += min(math.log1p(backlinks) * 2.0, 15.0)

        age = float(features_dict.get('brand_age_months', 12.0))
        score += min(age / 12.0, 5.0)

        return min(max(score, 0.0), 100.0)

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
