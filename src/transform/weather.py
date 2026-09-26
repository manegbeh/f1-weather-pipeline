import pandas as pd
import json
from pathlib import Path


def transform_weather(input_path, output_path):

    # 1. Open raw JSON
    with open(input_path, "r") as file:
        data = json.load(file)

    # 2. Extract the hourly section
    hourly_data = data["hourly"]

    # 3. Convert it into a DataFrame
    df = pd.DataFrame(hourly_data)

    # 4. Convert time to UTC datetime
    df["time"] = pd.to_datetime(
        df["time"],
        format="ISO8601",
        utc=True
    )

    # 5. Define candidate key
    key_columns = [
        "time"
    ]

    # 6. Validate duplicates
    duplicate_time = df.duplicated(subset=key_columns).sum()

    if duplicate_time > 0:
        raise ValueError(
            f"Found {duplicate_time} duplicate time records."
    )

    # 7. Validate missing candidate keys

    missing_keys = df[key_columns].isnull().sum()
    if (missing_keys > 0).any():
        raise ValueError(
            f"Missing values found in weather key columns:\n{missing_keys}"
        )

    # 8. Create output directory
    Path(output_path).parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # 9. Save as Parquet
    df.to_parquet(output_path, index=False)

    # 10. Print useful information
    print("Shape:", df.shape)
    print(df.head())
    print(df.dtypes)
    print("Saved to:", output_path)


if __name__ == "__main__":
    transform_weather(
        "data/raw/weather/weather_2024-11-03.json",
        "data/processed/weather/weather_2024-11-03.parquet"
    )
