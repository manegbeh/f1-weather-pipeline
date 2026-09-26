import duckdb
import pandas as pd

database_path = "data/warehouse/f1_weather.duckdb"

conn = duckdb.connect(database_path)


# -----------------------------
# Important race-status events
# -----------------------------

race_status_events = conn.execute("""
    SELECT
        date,
        lap_number,
        category,
        flag,
        message

    FROM race_control

    WHERE category IN (
        'SafetyCar',
        'SessionStatus'
    )
    OR flag = 'RED'
    OR message = 'TRACK CLEAR'

    ORDER BY date;
""").fetchdf()


print("\nRace-status events:")
print(race_status_events.to_string(index=False))

# -----------------------------
# Build race-state timeline
# -----------------------------

current_state = "NOT_STARTED"
state_changes = []

for _, event in race_status_events.iterrows():

    message = event["message"]
    event_time = event["date"]

    new_state = current_state

    if message == "SESSION STARTED":
        new_state = "NORMAL"

    elif message == "VIRTUAL SAFETY CAR DEPLOYED":
        new_state = "VSC"

    elif message == "VIRTUAL SAFETY CAR ENDING":
        new_state = "NORMAL"

    elif message == "SAFETY CAR DEPLOYED":
        new_state = "SAFETY_CAR"

    elif message == "SESSION ABORTED":
        new_state = "RED_FLAG"

    elif message == "RED FLAG":
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
                "date": event_time,
                "previous_state": current_state,
                "race_state": new_state,
                "trigger": message
            }
        )

        current_state = new_state

state_changes_df = pd.DataFrame(state_changes)

print("\nRace-state timeline:")
print(state_changes_df.to_string(index=False))

# -----------------------------
# Build race-state periods
# -----------------------------

state_periods = []

for i in range(len(state_changes_df) - 1):

    current_row = state_changes_df.iloc[i]
    next_row = state_changes_df.iloc[i + 1]

    state_periods.append(
        {
            "start_time": current_row["date"],
            "end_time": next_row["date"],
            "race_state": current_row["race_state"]
        }
    )


state_periods_df = pd.DataFrame(state_periods)


print("\nRace-state periods:")
print(state_periods_df.to_string(index=False))

# -----------------------------
# Get lap intervals
# -----------------------------

laps = conn.execute("""
    SELECT
        driver_number,
        lap_number,
        date_start,
        lap_duration,

        date_start
            + lap_duration * INTERVAL '1 second'
            AS date_end

    FROM laps

    WHERE date_start IS NOT NULL
        AND lap_duration IS NOT NULL

    ORDER BY
        date_start;
""").fetchdf()


print("\nLap intervals:")
print(laps.head(10).to_string(index=False))

# -----------------------------
# Find laps affected by neutralisation
# -----------------------------

neutralised_laps = conn.execute("""
    WITH lap_intervals AS (
        SELECT
            session_key,
            driver_number,
            lap_number,
            date_start,
            lap_duration,

            date_start
                + lap_duration * INTERVAL '1 second'
                AS date_end

        FROM laps

        WHERE date_start IS NOT NULL
            AND lap_duration IS NOT NULL
    ),

    neutralised_periods AS (
        SELECT
            TIMESTAMPTZ '2024-11-03 16:28:21+00:00' AS start_time,
            TIMESTAMPTZ '2024-11-03 16:29:50+00:00' AS end_time,
            'VSC' AS race_state

        UNION ALL

        SELECT
            TIMESTAMPTZ '2024-11-03 16:32:53+00:00',
            TIMESTAMPTZ '2024-11-03 16:37:21.752+00:00',
            'SAFETY_CAR'

        UNION ALL

        SELECT
            TIMESTAMPTZ '2024-11-03 16:37:21.752+00:00',
            TIMESTAMPTZ '2024-11-03 17:02:00.390+00:00',
            'RED_FLAG'

        UNION ALL

        SELECT
            TIMESTAMPTZ '2024-11-03 17:13:14+00:00',
            TIMESTAMPTZ '2024-11-03 17:19:29+00:00',
            'SAFETY_CAR'
    )

    SELECT
        l.driver_number,
        l.lap_number,
        l.date_start,
        l.date_end,
        n.race_state

    FROM lap_intervals l

    JOIN neutralised_periods n
        ON l.date_start < n.end_time
        AND l.date_end > n.start_time

    ORDER BY
        l.lap_number,
        l.driver_number;
""").fetchdf()


print("\nLaps affected by neutralisation:")
print(neutralised_laps.to_string(index=False))

unique_affected_laps = (
    neutralised_laps[
        ["driver_number", "lap_number"]
    ]
    .drop_duplicates()
)

print(
    "\nOverlap records:",
    len(neutralised_laps)
)

print(
    "Unique affected driver-laps:",
    len(unique_affected_laps)
)
conn.close()