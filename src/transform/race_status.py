import pandas as pd
from pathlib import Path


# -----------------------------
# Paths
# -----------------------------

input_path = (
    "data/processed/openf1/"
    "session_9636_race_control.parquet"
)

output_path = (
    "data/processed/openf1/"
    "session_9636_race_status.parquet"
)


# -----------------------------
# Load race-control data
# -----------------------------

df = pd.read_parquet(input_path)

df = df.sort_values("date")


# -----------------------------
# Select race-state events
# -----------------------------

race_events = df[
    (df["category"].isin(["SafetyCar", "SessionStatus"]))
    | (df["flag"] == "RED")
    | (df["message"] == "TRACK CLEAR")
].copy()


# -----------------------------
# Build state changes
# -----------------------------

current_state = "NOT_STARTED"
state_changes = []

for _, event in race_events.iterrows():

    message = event["message"]
    new_state = current_state

    if message == "SESSION STARTED":
        new_state = "NORMAL"

    elif message == "VIRTUAL SAFETY CAR DEPLOYED":
        new_state = "VSC"

    elif message == "VIRTUAL SAFETY CAR ENDING":
        new_state = "NORMAL"

    elif message == "SAFETY CAR DEPLOYED":
        new_state = "SAFETY_CAR"

    elif message in [
        "SESSION ABORTED",
        "RED FLAG"
    ]:
        new_state = "RED_FLAG"

    elif (
        message == "TRACK CLEAR"
        and current_state == "SAFETY_CAR"
    ):
        new_state = "NORMAL"

    elif message == "SESSION FINISHED":
        new_state = "FINISHED"

    if new_state != current_state:

        state_changes.append(
            {
                "start_time": event["date"],
                "race_state": new_state,
                "trigger": message
            }
        )

        current_state = new_state


state_changes_df = pd.DataFrame(state_changes)


# -----------------------------
# Convert changes into periods
# -----------------------------

state_periods = []

for i in range(len(state_changes_df) - 1):

    current_row = state_changes_df.iloc[i]
    next_row = state_changes_df.iloc[i + 1]

    state_periods.append(
        {
            "start_time": current_row["start_time"],
            "end_time": next_row["start_time"],
            "race_state": current_row["race_state"],
            "trigger": current_row["trigger"]
        }
    )


state_periods_df = pd.DataFrame(state_periods)


# -----------------------------
# Validate
# -----------------------------

print("Race-state periods:")
print(state_periods_df.to_string(index=False))

print(
    "\nNumber of periods:",
    len(state_periods_df)
)

if (
    state_periods_df["start_time"]
    >= state_periods_df["end_time"]
).any():
    raise ValueError(
        "Race-state period has an invalid time range"
    )


# -----------------------------
# Save
# -----------------------------

Path(output_path).parent.mkdir(
    parents=True,
    exist_ok=True
)

state_periods_df.to_parquet(
    output_path,
    index=False
)

print("\nSaved to:", output_path)