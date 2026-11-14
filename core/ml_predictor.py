
import json
import math
from pathlib import Path

import joblib
import pandas as pd
from django.conf import settings


# ---------------------------------------------------------
# Model and baseline file locations
# ---------------------------------------------------------

MODEL_DIR = Path(settings.BASE_DIR) / "ml_models"

MODEL_PATH = MODEL_DIR / "recoveriq_ridge_practical_v1.pkl"

BASELINE_PATH = MODEL_DIR / "recoveriq_baseline_v1.json"


# ---------------------------------------------------------
# Historical training ranges
# ---------------------------------------------------------

# These ranges represent the historical values used
# to train the model.
#
# They are not recommended operating conditions.

TRAINING_RANGES = {
    "DOSE Mg Flow LPM": (0.119, 0.809),

    "DOSE Na Flow LPM": (0.117, 0.710),

    "FEED OP mM": (
        60.607 / 30.973762,
        175.021 / 30.973762,
    ),

    "Temperature C": (10.272, 22.701),
}


# ---------------------------------------------------------
# Predict phosphorus conversion
# ---------------------------------------------------------

def predict_conversion(overrides=None):
    """
    Predict phosphorus conversion using the trained
    30-feature Ridge Regression model.

    Parameters
    ----------
    overrides : dict, optional
        Dictionary containing user-adjusted operating
        conditions that replace baseline feature values.

    Returns
    -------
    float
        Predicted phosphorus conversion as a fraction
        between 0 and 1.

    Raises
    ------
    ValueError
        If an unknown feature is supplied, feed OP is
        physically inconsistent with feed TP, or the
        model produces an impossible conversion.
    """

    # -----------------------------------------------------
    # STEP 1: Load trained model and scalers
    # -----------------------------------------------------

    bundle = joblib.load(MODEL_PATH)

    model = bundle["model"]
    x_scaler = bundle["xscaler"]
    y_scaler = bundle["yscaler"]
    features = bundle["features"]

    # -----------------------------------------------------
    # STEP 2: Load historical baseline
    # -----------------------------------------------------

    with open(BASELINE_PATH, "r") as f:
        baseline = json.load(f)

    # Copy baseline feature values
    input_values = baseline["features"].copy()

    # -----------------------------------------------------
    # STEP 3: Apply user-adjusted operating conditions
    # -----------------------------------------------------

    if overrides:

        unknown = set(overrides) - set(features)

        if unknown:
            raise ValueError(
                f"Unknown model features: {sorted(unknown)}"
            )

        # Update baseline with selected operating values
        input_values.update(overrides)

        # -------------------------------------------------
        # Recalculate derived features if feed OP changes
        # -------------------------------------------------

        if "FEED OP mM" in overrides:

            feed_op = float(input_values["FEED OP mM"])

            feed_tp = float(input_values["FEED TP mM"])

            # Recover baseline magnesium concentration
            # from baseline Mg:P ratio and baseline OP

            feed_mg = (
                float(baseline["features"]["FEED Mg:P"])
                * float(baseline["features"]["FEED OP mM"])
            )

            # Check physically meaningful concentrations
            if not (0 < feed_op <= feed_tp):

                raise ValueError(
                    "Feed orthophosphate must be greater "
                    "than zero and cannot exceed the "
                    "fixed baseline total phosphorus."
                )

            # Update dependent model features

            input_values["FEED InvOP"] = 1.0 / feed_op

            input_values["FEED Mg:P"] = (
                feed_mg / feed_op
            )

            input_values["FEED TP-OP mM"] = (
                feed_tp - feed_op
            )

    # -----------------------------------------------------
    # STEP 4: Build model input in correct feature order
    # -----------------------------------------------------

    X = pd.DataFrame(
        [
            {
                feature: input_values[feature]
                for feature in features
            }
        ],
        columns=features,
    )

    # -----------------------------------------------------
    # STEP 5: Scale inputs and generate prediction
    # -----------------------------------------------------

    X_scaled = x_scaler.transform(X)

    y_scaled = model.predict(X_scaled)

    prediction = y_scaler.inverse_transform(
        y_scaled.reshape(-1, 1)
    )[0, 0]

    prediction = float(prediction)

    # -----------------------------------------------------
    # STEP 6: Validate physical conversion limits
    # -----------------------------------------------------

    # Phosphorus conversion must be between 0 and 1.
    #
    # Do not clip predictions because clipping would
    # conceal model extrapolation or invalid predictions.

    if not math.isfinite(prediction):
        raise ValueError(
            "The ML model produced a non-finite "
            "phosphorus conversion prediction."
        )

    if not (0.0 <= prediction <= 1.0):

        raise ValueError(
            "The ML model predicted phosphorus conversion "
            "outside the physically meaningful range "
            "of 0–100%. This prediction is not valid "
            "and cannot be saved."
        )

    # -----------------------------------------------------
    # STEP 7: Return valid prediction
    # -----------------------------------------------------

    return prediction


# ---------------------------------------------------------
# Check historical training ranges
# ---------------------------------------------------------

def check_training_ranges(overrides):
    """
    Return warning messages for operating inputs
    outside historical training ranges.

    This function only identifies out-of-range inputs.

    The simulator view is responsible for rejecting
    unsupported scenarios before running predictions.
    """

    warnings = []

    for feature, value in overrides.items():

        if feature not in TRAINING_RANGES:
            continue

        minimum, maximum = TRAINING_RANGES[feature]

        value = float(value)

        # Reject non-finite values
        if not math.isfinite(value):

            warnings.append(
                f"{feature}: input must be a finite number."
            )

            continue

        # Check historical range
        if value < minimum or value > maximum:

            warnings.append(
                f"{feature}: {value:.3f} is outside the "
                f"historical training range "
                f"({minimum:.3f}–{maximum:.3f})."
            )

    return warnings
