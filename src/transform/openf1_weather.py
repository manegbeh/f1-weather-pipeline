import json
import pandas as pd
from pathlib import Path


def transform_openf1_weather(input_path, output_path):

    # 1. Load raw JSON
    with open(input_path, "r") as file:
        data = json.load(file)

    # 2. Convert to DataFrame
    df = pd.DataFrame(data)

    # 3. Convert timestamp to UTC datetime
    df["date"] = pd.to_datetime(
        df["date"],
        format="ISO8601",
        utc=True
    )

    # 4. Define candidate key
    key_columns = [
        "session_key",
        "date"
    ]

    # 5. Validate duplicate keys
    duplicate_date = df.duplicated(subset=key_columns).sum()

    if duplicate_date > 0:
        raise ValueError(
            f"Found {duplicate_date} duplicate weather records."
        )

    # 6. Validate missing keys
    missing_keys = df[key_columns].isnull().sum()

    if (missing_keys > 0).any():
        raise ValueError(
            f"Missing values found in weather key columns:\n{missing_keys}"
        )

    # 7. Create processed directory
    Path(output_path).parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # 8. Save processed data
    df.to_parquet(
        output_path,
        index=False
    )

    # 9. Confirmation
    print("Shape:", df.shape)
    print(df.head())
    print(df.dtypes)
    print("Saved to:", output_path)


if __name__ == "__main__":
    transform_openf1_weather(
        "data/raw/openf1/session_9636_weather.json",
        "data/processed/openf1/session_9636_weather.parquet"
    )