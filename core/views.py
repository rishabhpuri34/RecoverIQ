
from django.shortcuts import render
from .models import Reactor, ReactorObservation


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
