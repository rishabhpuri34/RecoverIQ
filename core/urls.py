from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("simulator/", views.simulator, name="simulator"),
    path("scenarios/", views.scenario_history, name="scenario_history"),
]