
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Reactor(models.Model):
    name = models.CharField(max_length=100)
    facility = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.facility} - {self.name}"


class ReactorObservation(models.Model):
    reactor = models.ForeignKey(
        Reactor,
        on_delete=models.CASCADE,
        related_name="observations"
    )

    timestamp = models.DateTimeField()

    conversion = models.FloatField(
        validators=[
            MinValueValidator(0),
            MaxValueValidator(1)
        ]
    )

    yield_value = models.FloatField(
        validators=[
            MinValueValidator(0),
            MaxValueValidator(1)
        ]
    )

    mgcl2_flow_lpm = models.FloatField(null=True, blank=True)
    naoh_flow_lpm = models.FloatField(null=True, blank=True)
    feed_op_mg_l = models.FloatField(null=True, blank=True)
    temperature_c = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ["-timestamp"]
        constraints = [
            models.UniqueConstraint(
                fields=["reactor", "timestamp"],
                name="unique_reactor_observation_timestamp"
            )
        ]

    def __str__(self):
        return f"{self.reactor.name} - {self.timestamp:%Y-%m-%d}"


class Scenario(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="scenarios"
    )

    reactor = models.ForeignKey(
        Reactor,
        on_delete=models.CASCADE,
        related_name="scenarios"
    )

    name = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)

    mgcl2_flow_lpm = models.FloatField(
        validators=[MinValueValidator(0)]
    )
    naoh_flow_lpm = models.FloatField(
        validators=[MinValueValidator(0)]
    )
    recycle_flow_lpm = models.FloatField(
        validators=[MinValueValidator(0)]
    )
    feed_op_mg_l = models.FloatField(
        validators=[MinValueValidator(0)]
    )
    temperature_c = models.FloatField()

    predicted_conversion = models.FloatField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(1)
        ]
    )

    predicted_yield = models.FloatField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(1)
        ]
    )

    model_version = models.CharField(
        max_length=50,
        blank=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.user.username})"
