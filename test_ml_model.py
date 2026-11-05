
import json
import joblib
import numpy as np
import sklearn
from pathlib import Path
import pandas as pd

# Locate model files
BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "ml_models"

# Load trained model
bundle = joblib.load(
    MODEL_DIR / "recoveriq_ridge_practical_v1.pkl"
)

# Load baseline observation
with open(
    MODEL_DIR / "recoveriq_baseline_v1.json"
) as f:
    baseline = json.load(f)

# Extract model components
model = bundle["model"]
x_scaler = bundle["xscaler"]
y_scaler = bundle["yscaler"]
features = bundle["features"]

# Arrange inputs in exact training feature order
# Create a DataFrame with the exact training feature names and order
X = pd.DataFrame(
    [{feature: baseline["features"][feature] for feature in features}],
    columns=features
)

# Scale, predict, and convert back to original units
X_scaled = x_scaler.transform(X)

prediction_scaled = model.predict(X_scaled)

prediction = y_scaler.inverse_transform(
    prediction_scaled.reshape(-1, 1)
)[0, 0]

print("scikit-learn version:", sklearn.__version__)
print("Model version:", bundle["model_version"])
print("Number of features:", len(features))
print("Baseline date:", baseline["observation_date"])
print(f"Predicted phosphorus conversion: {prediction:.2%}")
