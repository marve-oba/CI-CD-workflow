import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, render_template, request, session

APP_VERSION = os.getenv("APP_VERSION", "dev")
SECRET_KEY_FILE = Path(os.getenv("SECRET_KEY_FILE", "/vault/secrets/flask-secret-key"))
REQUEST_TIMEOUT = float(os.getenv("WEATHER_API_TIMEOUT", "8"))


def load_secret_key():
    if SECRET_KEY_FILE.is_file():
        value = SECRET_KEY_FILE.read_text(encoding="utf-8").strip()
        if value:
            return value, "vault-file"
    return "local-development-only-change-me", "local-fallback"


SECRET_KEY, SECRET_SOURCE = load_secret_key()

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")

WEATHER_CODES = {
    0: ("Clear sky", "clear"),
    1: ("Mainly clear", "clear"),
    2: ("Partly cloudy", "cloud"),
    3: ("Overcast", "cloud"),
    45: ("Fog", "fog"),
    48: ("Rime fog", "fog"),
    51: ("Light drizzle", "rain"),
    53: ("Drizzle", "rain"),
    55: ("Heavy drizzle", "rain"),
    56: ("Freezing drizzle", "ice"),
    57: ("Heavy freezing drizzle", "ice"),
    61: ("Light rain", "rain"),
    63: ("Rain", "rain"),
    65: ("Heavy rain", "rain"),
    66: ("Freezing rain", "ice"),
    67: ("Heavy freezing rain", "ice"),
    71: ("Light snow", "snow"),
    73: ("Snow", "snow"),
    75: ("Heavy snow", "snow"),
    77: ("Snow grains", "snow"),
    80: ("Rain showers", "rain"),
    81: ("Rain showers", "rain"),
    82: ("Heavy rain showers", "rain"),
    85: ("Snow showers", "snow"),
    86: ("Heavy snow showers", "snow"),
    95: ("Thunderstorm", "storm"),
    96: ("Thunderstorm with hail", "storm"),
    99: ("Thunderstorm with heavy hail", "storm"),
}


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "atmos-weather-lab/2.0"})
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
        return json.loads(response.read().decode("utf-8"))


def as_float(value, field, minimum=None, maximum=None):
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid {field}") from exc
    if minimum is not None and number < minimum:
        raise ValueError(f"Invalid {field}")
    if maximum is not None and number > maximum:
        raise ValueError(f"Invalid {field}")
    return number


def resolve_city(city):
    city = city.strip()
    if not city or len(city) > 80:
        raise ValueError("Enter a valid city name")

    query = urllib.parse.urlencode({"name": city, "count": 1, "language": "en", "format": "json"})
    data = fetch_json(f"https://geocoding-api.open-meteo.com/v1/search?{query}")
    results = data.get("results") or []
    if not results:
        raise ValueError("Location not found")

    first = results[0]
    label = ", ".join(part for part in (first.get("name"), first.get("admin1"), first.get("country")) if part)
    return as_float(first.get("latitude"), "latitude", -90, 90), as_float(first.get("longitude"), "longitude", -180, 180), label


def condition_for(code):
    return WEATHER_CODES.get(code, (f"Weather code {code}", "cloud"))


def cardinal_direction(degrees):
    if degrees is None:
        return "—"
    names = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    return names[round(float(degrees) / 45) % 8]


def make_flash_reports(current, today):
    reports = []
    temp = current.get("temperature_c")
    feels = current.get("apparent_temperature_c")
    gusts = current.get("wind_gusts_kmh")
    precip = today.get("precipitation_probability_max")
    uv = today.get("uv_index_max")
    code = current.get("weather_code")

    if code in {95, 96, 99}:
        reports.append({"level": "attention", "title": "Convective weather", "text": "Thunderstorm conditions are present in the current weather code."})
    if gusts is not None and gusts >= 50:
        reports.append({"level": "attention", "title": "Strong gust signal", "text": f"Current gusts are near {round(gusts)} km/h. Secure loose outdoor items."})
    if precip is not None and precip >= 70:
        reports.append({"level": "watch", "title": "Rain window", "text": f"Today's maximum precipitation probability is {round(precip)}%."})
    if uv is not None and uv >= 6:
        reports.append({"level": "watch", "title": "Elevated UV", "text": f"Today's forecast UV index peaks near {uv:.1f}."})
    if temp is not None and temp >= 32:
        reports.append({"level": "attention", "title": "Heat signal", "text": f"Temperature is {temp:.1f}°C with a feels-like value of {feels:.1f}°C."})
    if temp is not None and temp <= 0:
        reports.append({"level": "watch", "title": "Freezing conditions", "text": f"Current temperature is {temp:.1f}°C."})

    if not reports:
        reports.append({"level": "clear", "title": "Steady conditions", "text": "No threshold-based condition summary is active from the current forecast values."})

    return reports[:3]


def select_hourly(hourly, current_time, count=8):
    times = hourly.get("time") or []
    start = 0
    if current_time in times:
        start = times.index(current_time)
    else:
        for index, item in enumerate(times):
            if item >= current_time:
                start = index
                break

    output = []
    fields = {
        "temperature_c": hourly.get("temperature_2m") or [],
        "precipitation_probability": hourly.get("precipitation_probability") or [],
        "weather_code": hourly.get("weather_code") or [],
    }

    for index in range(start, min(start + count, len(times))):
        code = fields["weather_code"][index] if index < len(fields["weather_code"]) else None
        label, theme = condition_for(code)
        output.append({
            "time": times[index],
            "temperature_c": fields["temperature_c"][index] if index < len(fields["temperature_c"]) else None,
            "precipitation_probability": fields["precipitation_probability"][index] if index < len(fields["precipitation_probability"]) else None,
            "weather_code": code,
            "condition": label,
            "theme": theme,
        })
    return output


def fetch_weather(latitude, longitude):
    current_fields = [
        "temperature_2m",
        "apparent_temperature",
        "relative_humidity_2m",
        "precipitation",
        "weather_code",
        "cloud_cover",
        "surface_pressure",
        "wind_speed_10m",
        "wind_direction_10m",
        "wind_gusts_10m",
    ]
    hourly_fields = ["temperature_2m", "precipitation_probability", "weather_code"]
    daily_fields = ["temperature_2m_max", "temperature_2m_min", "sunrise", "sunset", "precipitation_probability_max", "uv_index_max"]
    query = urllib.parse.urlencode({
        "latitude": latitude,
        "longitude": longitude,
        "current": ",".join(current_fields),
        "hourly": ",".join(hourly_fields),
        "daily": ",".join(daily_fields),
        "forecast_days": 2,
        "temperature_unit": "celsius",
        "wind_speed_unit": "kmh",
        "timezone": "auto",
    })
    data = fetch_json(f"https://api.open-meteo.com/v1/forecast?{query}")
    current_raw = data.get("current") or {}
    daily_raw = data.get("daily") or {}
    hourly_raw = data.get("hourly") or {}
    if not current_raw:
        raise ValueError("Weather data is unavailable")

    code = current_raw.get("weather_code")
    condition, theme = condition_for(code)
    current = {
        "temperature_c": current_raw.get("temperature_2m"),
        "apparent_temperature_c": current_raw.get("apparent_temperature"),
        "relative_humidity": current_raw.get("relative_humidity_2m"),
        "precipitation_mm": current_raw.get("precipitation"),
        "weather_code": code,
        "condition": condition,
        "theme": theme,
        "cloud_cover": current_raw.get("cloud_cover"),
        "surface_pressure_hpa": current_raw.get("surface_pressure"),
        "wind_speed_kmh": current_raw.get("wind_speed_10m"),
        "wind_direction_degrees": current_raw.get("wind_direction_10m"),
        "wind_direction": cardinal_direction(current_raw.get("wind_direction_10m")),
        "wind_gusts_kmh": current_raw.get("wind_gusts_10m"),
        "observed_at": current_raw.get("time"),
    }

    def day_at(index):
        def pick(key):
            values = daily_raw.get(key) or []
            return values[index] if index < len(values) else None
        return {
            "date": pick("time"),
            "high_c": pick("temperature_2m_max"),
            "low_c": pick("temperature_2m_min"),
            "sunrise": pick("sunrise"),
            "sunset": pick("sunset"),
            "precipitation_probability_max": pick("precipitation_probability_max"),
            "uv_index_max": pick("uv_index_max"),
        }

    today = day_at(0)
    tomorrow = day_at(1)
    return {
        "timezone": data.get("timezone"),
        "timezone_abbreviation": data.get("timezone_abbreviation"),
        "current": current,
        "today": today,
        "tomorrow": tomorrow,
        "hourly": select_hourly(hourly_raw, current_raw.get("time") or ""),
        "flash_reports": make_flash_reports(current, today),
    }


@app.after_request
def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    if request.path.startswith("/api/") or request.path == "/healthz":
        response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/")
def index():
    return render_template("index.html", app_version=APP_VERSION, last_location=session.get("last_location"))


@app.get("/healthz")
def healthz():
    return jsonify({"status": "ok", "version": APP_VERSION, "secret_source": SECRET_SOURCE})


@app.get("/api/weather")
def weather():
    city = (request.args.get("city") or "").strip()
    lat = request.args.get("lat")
    lon = request.args.get("lon")

    try:
        if city:
            latitude, longitude, label = resolve_city(city)
        elif lat is not None and lon is not None:
            latitude = as_float(lat, "latitude", -90, 90)
            longitude = as_float(lon, "longitude", -180, 180)
            label = f"{latitude:.4f}, {longitude:.4f}"
        else:
            return jsonify({"error": "Provide a city or latitude/longitude"}), 400

        data = fetch_weather(latitude, longitude)
        session["last_location"] = label
        return jsonify({
            "location": {"label": label, "latitude": latitude, "longitude": longitude},
            **data,
            "source": {"name": "Open-Meteo", "generated_at": datetime.now(timezone.utc).isoformat()},
        })
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
        app.logger.warning("Weather upstream error: %s", exc)
        return jsonify({"error": "Weather service is temporarily unavailable"}), 502


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
