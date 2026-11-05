
from django.shortcuts import render
from .models import Reactor, ReactorObservation
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import ScenarioForm
from .models import Reactor, ReactorObservation, Scenario
from .ml_predictor import predict_conversion, check_training_ranges
from django.contrib import messages


def dashboard(request):
    latest_observation = (
        ReactorObservation.objects
        .select_related("reactor")
        .order_by("-timestamp")
        .first()
    )

    context = {
        "app_name": "RecoverIQ",
        "tagline": "Clearer insights. Smarter recovery.",
        "reactor_count": Reactor.objects.count(),
        "observation_count": ReactorObservation.objects.count(),
        "latest_observation": latest_observation,
    }

    return render(request, "core/dashboard.html", context)



@login_required(login_url="/admin/login/")
def simulator(request):
    if request.method == "POST":
        form = ScenarioForm(request.POST)

        if form.is_valid():
            scenario = form.save(commit=False)
            scenario.user = request.user

            # Map form inputs to model feature names.
            # Only MgCl2 and NaOH dosing are used at this stage.

            # Convert feed orthophosphate from mg/L as P to mM
            feed_op_mM = float(scenario.feed_op_mg_l) / 30.973762

            overrides = {
                "DOSE Mg Flow LPM": float(scenario.mgcl2_flow_lpm),
                "DOSE Na Flow LPM": float(scenario.naoh_flow_lpm),
                "FEED OP mM": feed_op_mM,
                "Temperature C": float(scenario.temperature_c),
            }
            warnings = check_training_ranges(overrides)
            scenario.prediction_warnings = warnings

            # Predict phosphorus conversion

            try:
                predicted_conversion = predict_conversion(
                    overrides=overrides
                )
            except ValueError as error:
                form.add_error("feed_op_mg_l", str(error))

                return render(
                    request,
                    "core/simulator.html",
                    {"form": form}
                )

            # Store model prediction in the scenario
            scenario.predicted_conversion = predicted_conversion
            scenario.baseline_conversion = predict_conversion()
            scenario.model_version = "ridge_practical_v1"

            # Save scenario and prediction

            scenario.save()


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

    return render(
        request,
        "core/scenario_history.html",
        {"scenarios": scenarios}
    )

