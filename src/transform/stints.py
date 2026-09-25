import json
import pandas as pd

def transform_stints(data):
    df = pd.DataFrame(data)
    df["valid_for_strategy"] = df["lap_start"].notna() & df["lap_end"].notna()

    stint_columns = [
        "meeting_key",
        "session_key",
        "driver_number",
        "stint_number",
        "lap_start",
        "lap_end",
        "compound",
        "tyre_age_at_start",
        "valid_for_strategy"
    ]
    
    clean_stints = df[stint_columns].copy()

    duplicate_stints = clean_stints.duplicated(
        subset =["session_key", "driver_number", "stint_number"]
    ).sum()    

    if duplicate_stints > 0:
            raise ValueError(
                f"Found {duplicate_stints} duplicate stint records."
            )

    key_columns = [
        "session_key",
        "driver_number",
        "stint_number"
    ]

    missing_keys = clean_stints[key_columns].isnull().sum()
    if (missing_keys > 0).any():
        raise ValueError(
            f"Missing values found in stint key columns:\n{missing_keys}"
                )
    
    return clean_stints


if __name__ == "__main__":
    filepath = "data/raw/openf1/session_9636_stints.json"

    with open(filepath, "r") as file:
        data = json.load(file)

    clean_stints = transform_stints(data)

    output_path = "data/processed/openf1/session_9636_stints.parquet"
    clean_stints.to_parquet(output_path, index=False)

    print(f"Saved processed stints to {output_path}")
    print(clean_stints.shape)
    print(clean_stints.dtypes)