
from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Reactor, Scenario
from unittest.mock import patch


class HomePageTests(TestCase):

    def test_homepage_loads_successfully(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_simulator_requires_login(self):
        response = self.client.get("/simulator/")
        self.assertEqual(response.status_code, 302)

    def test_scenario_history_requires_login(self):
        response = self.client.get("/scenarios/")
        self.assertEqual(response.status_code, 302)


class ScenarioPrivacyTests(TestCase):

    def test_users_cannot_see_other_users_scenarios(self):
        User = get_user_model()

        user_a = User.objects.create_user(
            username="user_a",
            password="TestPassword123!"
        )

        user_b = User.objects.create_user(
            username="user_b",
            password="TestPassword123!"
        )

        reactor = Reactor.objects.create(
            name="Test Reactor",
            facility="Test Facility"
        )

        Scenario.objects.create(
            user=user_a,
            reactor=reactor,
            name="Private Scenario A",
            mgcl2_flow_lpm=0.4,
            naoh_flow_lpm=0.3,
            recycle_flow_lpm=100,
            feed_op_mg_l=110,
            temperature_c=16,
            predicted_conversion=0.45
        )

        # Log in as User B
        self.client.force_login(user_b)

        # Request scenario history
        response = self.client.get("/scenarios/")

        self.assertEqual(response.status_code, 200)

        # User B must not see User A's scenario
        self.assertNotContains(
            response,
            "Private Scenario A"
        )


class ScenarioPredictionTests(TestCase):

    @patch("core.views.check_training_ranges", return_value=[])
    @patch("core.views.predict_conversion")
    def test_scenario_prediction_is_saved(
        self, mock_predict, mock_ranges
    ):
        User = get_user_model()

        user = User.objects.create_user(
            username="test_operator",
            password="TestPassword123!"
        )

        reactor = Reactor.objects.create(
            name="Test Reactor",
            facility="Test Facility"
        )

        self.client.force_login(user)

        # First prediction is the scenario;
        # second prediction is the baseline.
        mock_predict.side_effect = [0.45, 0.40]

        response = self.client.post(
            "/simulator/",
            {
                "reactor": reactor.id,
                "name": "Higher Magnesium Test",
                "mgcl2_flow_lpm": 0.42,
                "naoh_flow_lpm": 0.45,
                "recycle_flow_lpm": 100,
                "feed_op_mg_l": 110,
                "temperature_c": 16,
            }
        )

        # Successful submission redirects to history.
        self.assertEqual(response.status_code, 302)

        # Verify that the scenario was saved.
        self.assertEqual(Scenario.objects.count(), 1)

        scenario = Scenario.objects.get()

        # Verify ownership and predicted values.
        self.assertEqual(scenario.user, user)
        self.assertEqual(scenario.reactor, reactor)
        self.assertAlmostEqual(
            scenario.predicted_conversion, 0.45
        )
        self.assertAlmostEqual(
            scenario.baseline_conversion, 0.40
        )

        # Verify that the prediction function ran twice.
        self.assertEqual(mock_predict.call_count, 2)

