import json
import pandas as pd


filepath = "data/raw/openf1/session_9636_race_control.json"

with open(filepath, "r") as file:
    data = json.load(file)

df = pd.DataFrame(data)

print("Shape:", df.shape)

print("\nColumns:")
print(df.columns.tolist())

print("\nData types:")
print(df.dtypes)

print("\nMissing values:")
print(df.isna().sum())

print("\nFirst 10 records:")
print(df.head(10).to_string(index=False))

# -----------------------------
# Inspect suspicious race periods
# -----------------------------

interesting_events = df[
    (
        df["lap_number"].between(24, 35)
    )
    |
    (
        df["lap_number"].between(37, 45)
    )
][
    [
        "date",
        "lap_number",
        "category",
        "flag",
        "scope",
        "sector",
        "message"
    ]
]

print("\nRace-control events during slow periods:")
print(
    interesting_events.to_string(
        index=False
    )
)