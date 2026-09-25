import json
import pandas as pd

def transform_pit_stops(data):
    df = pd.DataFrame(data)

    df["valid_stop_duration"] = df["stop_duration"].notna()

    df["date"] = pd.to_datetime(
        df["date"],
        format="ISO8601",
        utc=True
    )

    pit_stop_columns = [
    "meeting_key",
    "session_key",
    "driver_number",
    "lap_number",
    "date",
    "lane_duration",
    "pit_duration",
    "stop_duration",
    "valid_stop_duration"
    ]

    clean_pit_stops = df[pit_stop_columns].copy()
   
    duplicate_pit_stops = clean_pit_stops.duplicated(
        subset=["session_key", "driver_number","lap_number"]
    ).sum()

    if duplicate_pit_stops > 0:
                raise ValueError(
                    f"Found {duplicate_pit_stops} duplicate pit stop records."
                )

    key_columns = [
            "session_key",
            "driver_number",
            "lap_number"
        ]
    missing_keys = clean_pit_stops[key_columns].isnull().sum()
    if (missing_keys > 0).any():
            raise ValueError(
                f"Missing values found in pit stop key columns:\n{missing_keys}"
            )

    return clean_pit_stops

if __name__ == "__main__":
    filepath = "data/raw/openf1/session_9636_pit_stops.json"

    with open(filepath, "r") as file:
        data = json.load(file)

    clean_pit_stops = transform_pit_stops(data)
    output_path = "data/processed/openf1/session_9636_pit_stops.parquet"
    clean_pit_stops.to_parquet(output_path, index=False)
    
    print(f"Saved processed pit stops to {output_path}")
    print(clean_pit_stops.shape)
    print(clean_pit_stops.dtypes)
    