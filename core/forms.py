
from django import forms
from .models import Scenario


class ScenarioForm(forms.ModelForm):
    class Meta:
        model = Scenario

        fields = [
            "reactor",
            "name",
            "mgcl2_flow_lpm",
            "naoh_flow_lpm",
            "recycle_flow_lpm",
            "feed_op_mg_l",
            "temperature_c",
        ]

        labels = {
            "reactor": "Select Reactor",
            "name": "Scenario Name",
            "mgcl2_flow_lpm": "MgCl₂ Dosing (L/min)",
            "naoh_flow_lpm": "NaOH Dosing (L/min)",
            "recycle_flow_lpm": "Recycle Flow (L/min)",
            "feed_op_mg_l": "Feed Orthophosphate (mg/L)",
            "temperature_c": "Temperature (°C)",
        }

        widgets = {
            "name": forms.TextInput(attrs={
                "placeholder": "e.g., Higher magnesium dosing"
            }),
            "mgcl2_flow_lpm": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "naoh_flow_lpm": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "recycle_flow_lpm": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "feed_op_mg_l": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "temperature_c": forms.NumberInput(attrs={"step": "0.1"}),
        }

    def clean(self):
        cleaned_data = super().clean()

        nonnegative_fields = [
            "mgcl2_flow_lpm",
            "naoh_flow_lpm",
            "recycle_flow_lpm",
            "feed_op_mg_l",
        ]

        for field in nonnegative_fields:
            value = cleaned_data.get(field)

            if value is not None and value < 0:
                self.add_error(
                    field,
                    "This value cannot be negative."
                )

        return cleaned_data
