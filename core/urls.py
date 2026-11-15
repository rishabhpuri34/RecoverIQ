from django.urls import path
from . import views

urlpatterns = [
    path("api/reactor-summary/", views.reactor_summary_api, name="reactor_summary_api"),
    path("", views.dashboard, name="dashboard"),
    path("simulator/", views.simulator, name="simulator"),
    path("scenarios/", views.scenario_history, name="scenario_history"),
    path("yield-prediction/", views.yield_prediction, name="yield_prediction"),
]