import os
import mlflow

def setup_mlflow():
    """Sets up MLflow tracking URI and experiment."""
    tracking_uri = "file://" + os.path.abspath("data/mlruns")
    if not os.path.exists("data/mlruns"):
        os.makedirs("data/mlruns", exist_ok=True)
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment("geo_intelligence")
    return tracking_uri
