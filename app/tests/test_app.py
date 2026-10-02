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


class WeatherTransportTests(unittest.TestCase):
    @patch.object(weather_app.http.client, "HTTPSConnection")
    def test_rejects_untrusted_urls_before_connecting(self, mock_connection):
        for url in (
            "file:///etc/passwd",
            "http://api.open-meteo.com/v1/forecast",
            "https://example.com/",
            "https://api.open-meteo.com:8443/",
            "https://user:password@api.open-meteo.com/",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                weather_app.fetch_json(url)
        mock_connection.assert_not_called()

    @patch.object(weather_app.http.client, "HTTPSConnection")
    def test_fetches_json_over_https_and_closes_connection(self, mock_connection):
        connection = mock_connection.return_value
        response = connection.getresponse.return_value
        response.status = 200
        response.read.return_value = b'{"temperature": 21}'
        result = weather_app.fetch_json("https://api.open-meteo.com/v1/forecast?latitude=43")
        self.assertEqual(result, {"temperature": 21})
        mock_connection.assert_called_once_with("api.open-meteo.com", timeout=weather_app.REQUEST_TIMEOUT)
        connection.request.assert_called_once_with(
            "GET", "/v1/forecast?latitude=43", headers={"User-Agent": "atmos-weather-lab/2.0"}
        )
        connection.close.assert_called_once()

    @patch.object(weather_app.http.client, "HTTPSConnection")
    def test_does_not_follow_redirects(self, mock_connection):
        connection = mock_connection.return_value
        connection.getresponse.return_value.status = 302
        with self.assertRaises(weather_app.urllib.error.URLError):
            weather_app.fetch_json("https://api.open-meteo.com/")
        connection.request.assert_called_once()
        connection.close.assert_called_once()

    @patch.object(weather_app.http.client, "HTTPSConnection")
    def test_network_failure_closes_connection(self, mock_connection):
        connection = mock_connection.return_value
        connection.request.side_effect = OSError("connection reset")
        with self.assertRaises(weather_app.urllib.error.URLError):
            weather_app.fetch_json("https://api.open-meteo.com/")
        connection.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
