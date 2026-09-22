import json
import requests


def extract_laps(session_key, driver_number):
    url = "https://api.openf1.org/v1/laps"

    params = {
        "session_key": session_key,
        "driver_number": driver_number
    }

    response = requests.get(
        url,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    return data


def save_raw_json(data, filepath):
    with open(filepath, "w") as file:
        json.dump(data, file, indent=4)


if __name__ == "__main__":
    laps = extract_laps(9161, 63)

    filepath = "data/raw/openf1/session_9161_driver_63_laps.json"

    save_raw_json(laps, filepath)

    print("Records extracted:", len(laps))
    print("Saved to:", filepath)