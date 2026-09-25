import json
import pandas as pd

def transform_drivers(data):
    df = pd.DataFrame(data)

    driver_columns = [
        "meeting_key",
        "session_key",
        "driver_number",
        "full_name",
        "name_acronym",
        "team_name",
        "team_colour",
        "country_code"
    ]

    clean_drivers = df[driver_columns].copy()
   
    duplicate_drivers = clean_drivers.duplicated(
        subset=["session_key", "driver_number"]
    ).sum()

    if duplicate_drivers > 0:
                raise ValueError(
                    f"Found {duplicate_drivers} duplicate driver records."
                )

    key_columns = [
            "session_key",
            "driver_number"
        ]
    missing_keys = clean_drivers[key_columns].isnull().sum()
    if (missing_keys > 0).any():
            raise ValueError(
                f"Missing values found in driver key columns:\n{missing_keys}"
            )

    return clean_drivers

if __name__ == "__main__":
    filepath = "data/raw/openf1/session_9636_drivers.json"

    with open(filepath, "r") as file:
        data = json.load(file)

    clean_drivers = transform_drivers(data)
    output_path = "data/processed/openf1/session_9636_drivers.parquet"
    clean_drivers.to_parquet(output_path, index=False)
    
    print(f"Saved processed drivers to {output_path}")
    print(clean_drivers.shape)
    print(clean_drivers.dtypes)