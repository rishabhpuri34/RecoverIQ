
from django.contrib import admin
from .models import Reactor, ReactorObservation, Scenario


@admin.register(Reactor)
class ReactorAdmin(admin.ModelAdmin):
    list_display = ("name", "facility", "active")
    search_fields = ("name", "facility")


@admin.register(ReactorObservation)
class ReactorObservationAdmin(admin.ModelAdmin):
    list_display = (
        "reactor",
        "timestamp",
        "conversion",
        "yield_value",
    )
    list_filter = ("reactor",)
    ordering = ("-timestamp",)


@admin.register(Scenario)
class ScenarioAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "user",
        "reactor",
        "created_at",
        "predicted_conversion",
    )
    list_filter = ("reactor", "created_at")
