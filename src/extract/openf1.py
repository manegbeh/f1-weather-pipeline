import json
import requests
from pathlib import Path

def extract_laps(session_key, driver_number=None):
    url = "https://api.openf1.org/v1/laps"

    params = {
        "session_key": session_key
    }

    if driver_number is not None:
        params["driver_number"] = driver_number

    response = requests.get(
        url,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    return data

def extract_stints(session_key):
    url = "https://api.openf1.org/v1/stints"

    params = {
            "session_key": session_key
        }

    response = requests.get(
            url,
            params=params,
            timeout=30
        )
    
    response.raise_for_status()
    
    return response.json()
    
def extract_pit_stops(session_key):
    url = "https://api.openf1.org/v1/pit"

    params = {
        "session_key": session_key
    }

    response = requests.get(
        url,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    return response.json()

def extract_drivers(session_key):
    url = "https://api.openf1.org/v1/drivers"

    params ={
        "session_key": session_key
    }

    response = requests.get(
        url,
        params = params,
        timeout=30
    )

    response.raise_for_status()

    return response.json()

def save_raw_json(data, filepath):
    with open(filepath, "w") as file:
        json.dump(data, file, indent=4)


def extract_sessions(year, session_name):
    url = "https://api.openf1.org/v1/sessions"

    params = {
        "year": year,
        "session_name": session_name
    }

    response = requests.get(
        url,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


if __name__ == "__main__":
    session_key = 9636
    
    laps_filepath = f"data/raw/openf1/session_{session_key}_laps.json"
    if Path(laps_filepath).exists():
        print("Laps already downloaded - skipping API request")
    else:
        laps = extract_laps(session_key)
        save_raw_json(laps, filepath)
        print("Race session:", session_key)
        print("Lap records extracted:", len(laps))
        print("Saved to:", filepath)
    
    stints_filepath = f"data/raw/openf1/session_{session_key}_stints.json"
    if Path(stints_filepath).exists():
        print("Stints already downloaded - skipping API request")
    else:
        stints = extract_stints(session_key)
        save_raw_json(stints, stints_filepath)
        print("Stint records extracted:", len(stints))
        print("Saved to:", stints_filepath)

    
    pit_stops_filepath = f"data/raw/openf1/session_{session_key}_pit_stops.json"
    if Path(pit_stops_filepath).exists():
        print("Pit Stops already downloaded - skipping API request")
    else:
        pit_stops = extract_pit_stops(session_key)
        save_raw_json(pit_stops, pit_stops_filepath)
        print("Pit stops extracted", len(pit_stops))
        print("Saved to:",pit_stops_filepath)

    
    drivers_filepath = f"data/raw/openf1/session_{session_key}_drivers.json"
    if Path(drivers_filepath).exists():
        print("Drivers already downloaded - skipping API request")
    else:
        drivers = extract_drivers(session_key)
        save_raw_json(drivers, drivers_filepath)
        print("Drivers extracted", len(drivers))
        print("Saved to:", drivers_filepath)