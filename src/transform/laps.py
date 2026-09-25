import json
import pandas as pd

def transform_laps(data):
    df = pd.DataFrame(data)

    df["date_start"] = pd.to_datetime(
        df["date_start"],
        format="ISO8601",
        utc=True
    )

    df["valid_for_weather"] = df["date_start"].notna()
    df["valid_for_pace"] = df["lap_duration"].notna()

    lap_columns = [
        "meeting_key",
        "session_key",
        "driver_number",
        "lap_number",
        "date_start",
        "lap_duration",
        "duration_sector_1",
        "duration_sector_2",
        "duration_sector_3",
        "is_pit_out_lap",
        "valid_for_weather",
        "valid_for_pace"
    ]

    clean_laps = df[lap_columns].copy()

    duplicate_laps = clean_laps.duplicated(
        subset=["session_key", "driver_number", "lap_number"]
    ).sum()

    if duplicate_laps > 0:
        raise ValueError(
            f"Found {duplicate_laps} duplicate lap records."
        )

    invalid_lap_numbers = (
        clean_laps["lap_number"] < 1
    ).sum()

    if invalid_lap_numbers > 0:
        raise ValueError(
            f"Found {invalid_lap_numbers} invalid lap numbers."
        )

    key_columns = [
        "session_key",
        "driver_number",
        "lap_number"
    ]
    missing_keys = clean_laps[key_columns].isnull().sum()
    if (missing_keys > 0).any():
        raise ValueError(
                    f"Missing values found in lap key columns:\n{missing_keys}"
                )
        

    return clean_laps

if __name__ == "__main__":
    filepath = "data/raw/openf1/session_9636_laps.json"

    with open(filepath, "r") as file:
        data = json.load(file)

    clean_laps = transform_laps(data)
    output_path = "data/processed/openf1/session_9636_laps.parquet"
    clean_laps.to_parquet(output_path, index=False)

    print(f"Saved processed laps to {output_path}")
    print(clean_laps.shape)
    print(clean_laps.dtypes)