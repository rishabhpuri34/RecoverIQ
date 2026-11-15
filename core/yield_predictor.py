
from pathlib import Path
import json

import numpy as np
import pandas as pd
from xgboost import Booster, DMatrix


# ==========================================================
# MODEL FILE LOCATIONS
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "ml_models"

MODEL_PATH = MODEL_DIR / "recoveriq_xgb_yield_v1.json"
METADATA_PATH = MODEL_DIR / "recoveriq_xgb_yield_metadata_v1.json"
BASELINE_PATH = MODEL_DIR / "recoveriq_xgb_yield_baseline_v1.json"


# ==========================================================
# LOAD MODEL ARTIFACTS
# ==========================================================

def load_yield_artifacts():

    for path in [
        MODEL_PATH,
        METADATA_PATH,
        BASELINE_PATH,
    ]:
        if not path.exists():
            raise FileNotFoundError(
                f"Required yield model file not found: {path}"
            )

    model = Booster()
    model.load_model(str(MODEL_PATH))

    with open(METADATA_PATH, "r") as file:
        metadata = json.load(file)

    with open(BASELINE_PATH, "r") as file:
        baseline = json.load(file)

    feature_names = metadata["feature_names"]

    if len(feature_names) != 43:
        raise ValueError(
            "Yield model must contain exactly 43 features."
        )

    missing = [
        name for name in feature_names
        if name not in baseline["features"]
    ]

    if missing:
        raise ValueError(
            f"Baseline is missing required features: {missing}"
        )

    return model, metadata, baseline


# ==========================================================
# PREPARE FEATURE VECTOR
# ==========================================================

def prepare_yield_features(feature_updates=None):

    _, metadata, baseline = load_yield_artifacts()

    features = baseline["features"].copy()

    if feature_updates is not None:

        unknown = [
            name for name in feature_updates
            if name not in features
        ]

        if unknown:
            raise ValueError(
                f"Unknown yield model features: {unknown}"
            )

        features.update(feature_updates)

    ordered_features = metadata["feature_names"]

    X = pd.DataFrame(
        [[features[name] for name in ordered_features]],
        columns=ordered_features,
    )

    X = X.apply(pd.to_numeric, errors="raise")

    if not np.isfinite(X.to_numpy(dtype=float)).all():
        raise ValueError(
            "Yield features contain invalid numeric values."
        )

    return X


# ==========================================================
# PREDICT YIELD
# ==========================================================

def predict_yield(feature_updates=None):

    model, metadata, baseline = load_yield_artifacts()

    X = prepare_yield_features(feature_updates)

    prediction = float(
        model.predict(
            DMatrix(X, feature_names=list(X.columns))
        )[0]
    )

    if not np.isfinite(prediction):
        raise ValueError(
            "Yield model returned a non-finite prediction."
        )

    if not 0 <= prediction <= 1:
        raise ValueError(
            "Yield prediction is outside the physical range 0-1."
        )

    return {
        "predicted_yield": prediction,
        "predicted_yield_percent": prediction * 100,
        "model_version": metadata["model_version"],
        "baseline_date": baseline["date"],
    }


# ==========================================================
# BASELINE PREDICTION
# ==========================================================

def predict_baseline_yield():

    return predict_yield()
