import sys
import unittest
from pathlib import Path
from unittest.mock import patch

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))

import app as weather_app


class WeatherAppTests(unittest.TestCase):
    def setUp(self):
        weather_app.app.config.update(TESTING=True, SECRET_KEY="test-only")
        self.client = weather_app.app.test_client()

    def test_home(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"ATMOS", response.data)

    def test_health(self):
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ok")

    def test_weather_requires_location(self):
        response = self.client.get("/api/weather")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "Provide a city or latitude/longitude")

    @patch.object(weather_app, "fetch_weather")
    @patch.object(weather_app, "resolve_city")
    def test_city_weather_response(self, mock_resolve, mock_fetch):
        mock_resolve.return_value = (43.6532, -79.3832, "Toronto, Ontario, Canada")
        mock_fetch.return_value = {
            "timezone": "America/Toronto",
            "timezone_abbreviation": "EDT",
            "current": {"temperature_c": 21, "condition": "Clear sky", "theme": "clear"},
            "today": {"high_c": 24, "low_c": 14},
            "tomorrow": {"high_c": 22, "low_c": 13},
            "hourly": [],
            "flash_reports": [{"level": "clear", "title": "Steady conditions", "text": "No threshold-based condition summary is active."}],
        }
        response = self.client.get("/api/weather?city=Toronto")
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["location"]["label"], "Toronto, Ontario, Canada")
        self.assertEqual(body["current"]["temperature_c"], 21)

    def test_flash_report_for_gusts(self):
        current = {"temperature_c": 20, "apparent_temperature_c": 20, "wind_gusts_kmh": 62, "weather_code": 2}
        today = {"precipitation_probability_max": 20, "uv_index_max": 3}
        reports = weather_app.make_flash_reports(current, today)
        self.assertEqual(reports[0]["title"], "Strong gust signal")


if __name__ == "__main__":
    unittest.main()
