
import json
import logging
import math
from pathlib import Path

from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from .models import Reactor, ReactorObservation, Scenario
from .forms import ScenarioForm
from .ml_predictor import predict_conversion, check_training_ranges


logger = logging.getLogger(__name__)

MODEL_VERSION = "ridge_practical_v1"
PHOSPHORUS_MG_PER_MMOL = 30.973762


def valid_conversion(value):
    """Check whether conversion is a finite fraction from 0 to 1."""
    if value is None:
        return False

    try:
        number = float(value)
        return math.isfinite(number) and 0.0 <= number <= 1.0
    except (ValueError, TypeError):
        return False


def get_baseline_feed_tp():
    """Load baseline Feed TP concentration in mM."""
    baseline_path = (
        Path(settings.BASE_DIR)
        / "ml_models"
        / "recoveriq_baseline_v1.json"
    )

    try:
        with open(baseline_path, "r") as file:
            baseline_data = json.load(file)

        return float(
            baseline_data["features"]["FEED TP mM"]
        )

    except (OSError, ValueError, TypeError, KeyError):
        logger.exception(
            "Could not load RecoverIQ baseline Feed TP"
        )
        return None


def get_scenario_overrides(scenario):
    """Convert saved scenario inputs into ML feature names."""
    return {
        "DOSE Mg Flow LPM": float(scenario.mgcl2_flow_lpm),
        "DOSE Na Flow LPM": float(scenario.naoh_flow_lpm),
        "FEED OP mM": (
            float(scenario.feed_op_mg_l)
            / PHOSPHORUS_MG_PER_MMOL
        ),
        "Temperature C": float(scenario.temperature_c),
    }


def scenario_inputs_supported(scenario, baseline_feed_tp):
    """Check historical ranges and physical Feed OP constraint."""
    try:
        overrides = get_scenario_overrides(scenario)

        if not all(
            math.isfinite(value)
            for value in overrides.values()
        ):
            return False

        if check_training_ranges(overrides):
            return False

        if baseline_feed_tp is None:
            return False

        feed_op = overrides["FEED OP mM"]

        if not (0 < feed_op <= baseline_feed_tp):
            return False

        return True

    except (ValueError, TypeError):
        return False


@login_required(login_url="/accounts/login/")
def dashboard(request):
    observations = (
        ReactorObservation.objects
        .select_related("reactor")
        .order_by("timestamp")
    )

    latest_observation = observations.last()
    recent_scenarios = []

    if request.user.is_authenticated:
        baseline_feed_tp = get_baseline_feed_tp()

        saved_scenarios = (
            Scenario.objects
            .filter(user=request.user)
            .select_related("reactor")
            .order_by("-created_at")
        )

        for scenario in saved_scenarios:
            if not valid_conversion(
                scenario.predicted_conversion
            ):
                continue

            if not valid_conversion(
                scenario.baseline_conversion
            ):
                continue

            if not scenario_inputs_supported(
                scenario,
                baseline_feed_tp
            ):
                continue

            recent_scenarios.append(scenario)

            if len(recent_scenarios) == 3:
                break

    context = {
        "app_name": "RecoverIQ",
        "tagline": "Clearer insights. Smarter recovery.",
        "reactor_count": Reactor.objects.count(),
        "observation_count": observations.count(),
        "latest_observation": latest_observation,
        "historical_observations": observations,
        "recent_scenarios": recent_scenarios,
    }

    return render(
        request,
        "core/dashboard.html",
        context
    )


@login_required(login_url="/accounts/login/")
def simulator(request):

    if request.method == "POST":
        form = ScenarioForm(request.POST)

        if form.is_valid():
            scenario = form.save(commit=False)
            scenario.user = request.user

            try:
                overrides = get_scenario_overrides(scenario)

                # STEP 1: Check historical training ranges.
                warnings = check_training_ranges(overrides)

                if warnings:
                    for warning in warnings:
                        form.add_error(None, str(warning))

                    return render(
                        request,
                        "core/simulator.html",
                        {"form": form}
                    )

                # STEP 2: Generate model predictions.
                predicted_conversion = predict_conversion(
                    overrides=overrides
                )

                baseline_conversion = predict_conversion()

            except (ValueError, TypeError) as error:
                form.add_error(None, str(error))

                return render(
                    request,
                    "core/simulator.html",
                    {"form": form}
                )

            except Exception:
                logger.exception(
                    "RecoverIQ prediction failed"
                )

                form.add_error(
                    None,
                    "The prediction could not be completed. "
                    "Please try again or contact the administrator."
                )

                return render(
                    request,
                    "core/simulator.html",
                    {"form": form}
                )

            # STEP 3: Validate predicted conversion.
            if not valid_conversion(predicted_conversion):
                form.add_error(
                    None,
                    "The model produced an invalid conversion. "
                    "This prediction cannot be saved."
                )

                return render(
                    request,
                    "core/simulator.html",
                    {"form": form}
                )

            if not valid_conversion(baseline_conversion):
                form.add_error(
                    None,
                    "The model baseline is invalid. "
                    "Please check the trained model."
                )

                return render(
                    request,
                    "core/simulator.html",
                    {"form": form}
                )

            # STEP 4: Save scenario and model metadata.
            scenario.predicted_conversion = predicted_conversion
            scenario.baseline_conversion = baseline_conversion
            scenario.prediction_warnings = []
            scenario.model_version = MODEL_VERSION

            scenario.save()

            # STEP 5: Verify the persisted model version.
            saved_model_version = (
                Scenario.objects
                .filter(pk=scenario.pk)
                .values_list("model_version", flat=True)
                .first()
            )

            if saved_model_version != MODEL_VERSION:
                logger.error(
                    "Model version mismatch for scenario %s: %r",
                    scenario.pk,
                    saved_model_version
                )
            else:
                logger.info(
                    "Scenario %s saved with model version %s",
                    scenario.pk,
                    saved_model_version
                )

            return redirect("scenario_history")

    else:
        form = ScenarioForm()

    return render(
        request,
        "core/simulator.html",
        {"form": form}
    )


@login_required
def scenario_history(request):
    scenarios = (
        Scenario.objects
        .filter(user=request.user)
        .select_related("reactor")
        .order_by("-created_at")
    )

    baseline_feed_tp = get_baseline_feed_tp()

    for scenario in scenarios:

        if scenario.predicted_conversion is None:
            scenario.display_status = "incomplete"

        elif not valid_conversion(
            scenario.predicted_conversion
        ):
            scenario.display_status = "invalid"

        elif scenario.baseline_conversion is None:
            scenario.display_status = "incomplete"

        elif not valid_conversion(
            scenario.baseline_conversion
        ):
            scenario.display_status = "invalid"

        elif not scenario_inputs_supported(
            scenario,
            baseline_feed_tp
        ):
            scenario.display_status = "unsupported"

        else:
            scenario.display_status = "within_ranges"

        # Saved scenario records are not modified.

    return render(
        request,
        "core/scenario_history.html",
        {"scenarios": scenarios}
    )

# Historical XGBoost yield prediction
@login_required
def yield_prediction(request):
    from .yield_predictor import predict_baseline_yield

    try:
        result = predict_baseline_yield()
        return render(
            request,
            "core/yield_prediction.html",
            {
                "prediction": result,
                "model_error": None,
            },
        )
    except Exception:
        logger.exception("Historical yield prediction failed")
        return render(
            request,
            "core/yield_prediction.html",
            {
                "prediction": None,
                "model_error": "The yield prediction is currently unavailable.",
            },
        )


@login_required(login_url="/accounts/login/")
def reactor_summary_api(request):
    from django.http import JsonResponse
    from django.db.models import Avg

    observations = ReactorObservation.objects.all()

    averages = observations.aggregate(
        average_conversion=Avg("conversion"),
        average_yield=Avg("yield_value"),
    )

    conversion = averages["average_conversion"]
    yield_value = averages["average_yield"]

    return JsonResponse({
        "reactor_count": Reactor.objects.count(),
        "observation_count": observations.count(),
        "average_conversion_percent": (
            round(conversion * 100, 2)
            if conversion is not None else None
        ),
        "average_yield_percent": (
            round(yield_value * 100, 2)
            if yield_value is not None else None
        ),
    })
