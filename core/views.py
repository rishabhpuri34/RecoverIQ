
from django.shortcuts import render
from .models import Reactor, ReactorObservation
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import ScenarioForm
from .models import Reactor, ReactorObservation, Scenario


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
            scenario.save()

            return redirect("scenario_history")

    else:
        form = ScenarioForm()

    return render(
        request,
        "core/simulator.html",
        {"form": form}
    )


@login_required(login_url="/admin/login/")
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

