import duckdb
from pathlib import Path


# -----------------------------
# Database setup
# -----------------------------

database_path = "data/warehouse/f1_weather.duckdb"

# Create the warehouse directory if it does not already exist
Path(database_path).parent.mkdir(parents=True, exist_ok=True)

# Connect to the DuckDB warehouse
conn = duckdb.connect(database_path)


# -----------------------------
# Load processed data
# -----------------------------

tables = {
    "drivers": "data/processed/openf1/session_9636_drivers.parquet",
    "laps": "data/processed/openf1/session_9636_laps.parquet",
    "stints": "data/processed/openf1/session_9636_stints.parquet",
    "pit_stops": "data/processed/openf1/session_9636_pit_stops.parquet",
    "openf1_weather": "data/processed/openf1/session_9636_weather.parquet",
    "openmeteo_weather": "data/processed/weather/weather_2024-11-03.parquet",
}

for table_name, file_path in tables.items():
    conn.execute(f"""
        CREATE OR REPLACE TABLE {table_name} AS
        SELECT *
        FROM read_parquet('{file_path}');
    """)

    print(f"Loaded: {table_name}")


# -----------------------------
# Build analytical model
# -----------------------------

conn.execute("""
    CREATE OR REPLACE TABLE lap_analysis AS

    SELECT
        -- Lap information
        l.meeting_key,
        l.session_key,
        l.driver_number,
        l.lap_number,
        l.date_start,
        l.lap_duration,
        l.duration_sector_1,
        l.duration_sector_2,
        l.duration_sector_3,
        l.is_pit_out_lap,
        l.valid_for_weather,
        l.valid_for_pace,

        -- Driver information
        d.full_name,
        d.name_acronym,
        d.team_name,
        d.team_colour,
        d.country_code,

        -- Tyre strategy information
        s.stint_number,
        s.compound,
        s.tyre_age_at_start,
        s.valid_for_strategy,

        -- Pit-stop information
        p.pit_duration,
        p.stop_duration,
        p.lane_duration,
        p.valid_stop_duration,

        CASE
            WHEN p.driver_number IS NOT NULL THEN TRUE
            ELSE FALSE
        END AS is_pit_stop,

        -- Weather information
        w.date AS weather_time,
        w.air_temperature,
        w.track_temperature,
        w.humidity,
        w.pressure,
        w.wind_speed,
        w.wind_direction,
        w.rainfall,

        -- Weather match quality
        l.date_start - w.date AS weather_time_gap,

        CASE
            WHEN l.date_start IS NOT NULL
                AND w.date IS NOT NULL
                AND l.date_start - w.date <= INTERVAL '60 seconds'
            THEN TRUE
            ELSE FALSE
        END AS valid_weather_match

    FROM laps l

    LEFT JOIN drivers d
        ON l.session_key = d.session_key
        AND l.driver_number = d.driver_number

    LEFT JOIN stints s
        ON l.session_key = s.session_key
        AND l.driver_number = s.driver_number
        AND l.lap_number BETWEEN s.lap_start AND s.lap_end

    LEFT JOIN pit_stops p
        ON l.session_key = p.session_key
        AND l.driver_number = p.driver_number
        AND l.lap_number = p.lap_number

    ASOF LEFT JOIN openf1_weather w
        ON l.session_key = w.session_key
        AND l.date_start >= w.date;
""")

print("Created: lap_analysis")


# -----------------------------
# Validate analytical model
# -----------------------------

validation = conn.execute("""
    SELECT
        COUNT(*) AS total_rows,

        COUNT(
            DISTINCT (session_key, driver_number, lap_number)
        ) AS unique_laps,

        SUM(
            CASE
                WHEN valid_for_pace THEN 1
                ELSE 0
            END
        ) AS valid_pace_laps,

        SUM(
            CASE
                WHEN valid_for_strategy THEN 1
                ELSE 0
            END
        ) AS valid_strategy_laps,

        SUM(
            CASE
                WHEN valid_weather_match THEN 1
                ELSE 0
            END
        ) AS valid_weather_laps,

        COUNT(*) FILTER (
            WHERE is_pit_stop
        ) AS pit_stop_laps

    FROM lap_analysis;
""").fetchdf()

print("\nValidation:")
print(validation.to_string(index=False))


# Make sure joins have not duplicated the lap-level grain
if validation.loc[0, "total_rows"] != validation.loc[0, "unique_laps"]:
    raise ValueError(
        "lap_analysis does not contain one unique row per driver lap"
    )


# -----------------------------
# Close database connection
# -----------------------------

conn.close()

print("\nDuckDB warehouse build complete")