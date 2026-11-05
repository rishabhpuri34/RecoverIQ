
import json
from pathlib import Path

import joblib
import pandas as pd
from django.conf import settings


MODEL_DIR = Path(settings.BASE_DIR) / "ml_models"

MODEL_PATH = MODEL_DIR / "recoveriq_ridge_practical_v1.pkl"
BASELINE_PATH = MODEL_DIR / "recoveriq_baseline_v1.json"

# Historical training ranges for operator-adjustable inputs
TRAINING_RANGES = {
    "DOSE Mg Flow LPM": (0.119, 0.809),
    "DOSE Na Flow LPM": (0.117, 0.710),
    "FEED OP mM": (
        60.607 / 30.973762,
        175.021 / 30.973762,
    ),
    "Temperature C": (10.272, 22.701),
}



def predict_conversion(overrides=None):
    """
    Predict phosphorus conversion using the trained
    30-feature Ridge Regression model.

    overrides: Optional dictionary containing operating
    conditions to replace in the baseline observation.
    """

    # Load trained model and scalers
    bundle = joblib.load(MODEL_PATH)

    model = bundle["model"]
    x_scaler = bundle["xscaler"]
    y_scaler = bundle["yscaler"]
    features = bundle["features"]

    # Load historical baseline
    with open(BASELINE_PATH, "r") as f:
        baseline = json.load(f)

    # Copy baseline features
    input_values = baseline["features"].copy()

    # Apply user-adjusted operating conditions
    if overrides:
        unknown = set(overrides) - set(features)
        if unknown:
            raise ValueError(
                f"Unknown model features: {sorted(unknown)}"
            )
        input_values.update(overrides)

        # Recalculate derived features if feed OP changes
        if "FEED OP mM" in overrides:
            feed_op = float(input_values["FEED OP mM"])
            feed_tp = float(input_values["FEED TP mM"])
            # Recover baseline Mg concentration from the original
            # baseline ratio and baseline OP concentration
            feed_mg = (
                    float(baseline["features"]["FEED Mg:P"])
                    * float(baseline["features"]["FEED OP mM"])
            )

            # Validate physically meaningful concentrations
            if not (0 < feed_op <= feed_tp):
                raise ValueError(
                    "Feed OP must be greater than zero "
                    "and cannot exceed feed TP."
                )

            input_values["FEED InvOP"] = 1.0 / feed_op
            input_values["FEED Mg:P"] = feed_mg / feed_op
            input_values["FEED TP-OP mM"] = feed_tp - feed_op

    # Ensure correct feature order
    X = pd.DataFrame(
        [{feature: input_values[feature] for feature in features}],
        columns=features
    )

    # Scale inputs and predict
    X_scaled = x_scaler.transform(X)
    y_scaled = model.predict(X_scaled)

    prediction = y_scaler.inverse_transform(
        y_scaled.reshape(-1, 1)
    )[0, 0]

    return float(prediction)

def check_training_ranges(overrides):
    """
    Return warnings for inputs outside historical training ranges.
    Predictions are still allowed.
    """
    warnings = []

    for feature, value in overrides.items():
        if feature not in TRAINING_RANGES:
            continue

        minimum, maximum = TRAINING_RANGES[feature]
        value = float(value)

        if value < minimum or value > maximum:
            warnings.append(
                f"{feature}: {value:.3f} is outside the "
                f"historical training range "
                f"({minimum:.3f}–{maximum:.3f})."
            )

    return warnings
