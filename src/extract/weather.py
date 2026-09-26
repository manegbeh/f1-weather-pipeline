import requests
import json
from pathlib import Path

BASE_URL = "https://archive-api.open-meteo.com/v1/archive"


def extract_weather(latitude, longitude, date):
    filepath = f"data/raw/weather/weather_{date}.json"

    Path(filepath).parent.mkdir(parents=True, exist_ok=True)

    if Path(filepath).exists():

        print("Weather already downloaded - skipping API request")

        return

    url = "https://archive-api.open-meteo.com/v1/archive"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": date,
        "end_date": date,
        "hourly": [
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "rain",
            "wind_speed_10m"
        ],
        "timezone": "GMT"
    }

    response = requests.get(
        BASE_URL,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    with open(filepath, "w") as file:
        json.dump(data, file, indent=2)

    print("Saved to:", filepath)

if __name__ == "__main__":
    extract_weather(
        latitude=-23.7036,
        longitude=-46.6997,
        date="2024-11-03"
    )