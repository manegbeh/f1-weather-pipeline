import duckdb
from pathlib import Path


# --------------------------------------------------
# Database setup
# --------------------------------------------------

database_path = "data/warehouse/f1_weather.duckdb"

Path(database_path).parent.mkdir(
    parents=True,
    exist_ok=True
)

conn = duckdb.connect(database_path)


# --------------------------------------------------
# Processed data sources
# --------------------------------------------------

tables = {
    "drivers": "data/processed/openf1/session_9636_drivers.parquet",
    "laps": "data/processed/openf1/session_9636_laps.parquet",
    "stints": "data/processed/openf1/session_9636_stints.parquet",
    "pit_stops": "data/processed/openf1/session_9636_pit_stops.parquet",
    "openf1_weather": "data/processed/openf1/session_9636_weather.parquet",
    "openmeteo_weather": "data/processed/weather/weather_2024-11-03.parquet",
    "race_control": "data/processed/openf1/session_9636_race_control.parquet",
    "race_status": "data/processed/openf1/session_9636_race_status.parquet",
}


# --------------------------------------------------
# Load processed Parquet files into DuckDB
# --------------------------------------------------

for table_name, file_path in tables.items():

    conn.execute(
        f"""
        CREATE OR REPLACE TABLE {table_name} AS
        SELECT *
        FROM read_parquet('{file_path}');
        """
    )

    print(f"Loaded: {table_name}")


# --------------------------------------------------
# Create analytical lap-level table
# --------------------------------------------------

conn.execute("""
    CREATE OR REPLACE TABLE lap_analysis AS

    WITH lap_base AS (

        SELECT
            l.meeting_key,
            l.session_key,
            l.driver_number,
            l.lap_number,

            l.date_start,

            l.date_start
                + l.lap_duration * INTERVAL '1 second'
                AS date_end,

            l.lap_duration,
            l.duration_sector_1,
            l.duration_sector_2,
            l.duration_sector_3,
            l.is_pit_out_lap,
            l.valid_for_weather,
            l.valid_for_pace,

            d.full_name,
            d.name_acronym,
            d.team_name,
            d.team_colour,
            d.country_code,

            s.stint_number,
            s.compound,
            s.tyre_age_at_start,
            s.valid_for_strategy,

            p.pit_duration,
            p.stop_duration,
            p.lane_duration,
            p.valid_stop_duration,

            CASE
                WHEN p.driver_number IS NOT NULL
                THEN TRUE
                ELSE FALSE
            END AS is_pit_stop,

            w.date AS weather_time,
            w.air_temperature,
            w.track_temperature,
            w.humidity,
            w.pressure,
            w.wind_speed,
            w.wind_direction,
            w.rainfall,

            l.date_start - w.date
                AS weather_time_gap,

            CASE
                WHEN l.date_start IS NOT NULL
                    AND w.date IS NOT NULL
                    AND l.date_start - w.date
                        <= INTERVAL '60 seconds'
                THEN TRUE
                ELSE FALSE
            END AS valid_weather_match,

            CASE
                WHEN l.date_start IS NULL
                    OR l.lap_duration IS NULL
                THEN NULL

                WHEN EXISTS (
                    SELECT 1
                    FROM race_status rs

                    WHERE rs.race_state != 'NORMAL'
                        AND l.date_start < rs.end_time
                        AND (
                            l.date_start
                            + l.lap_duration
                                * INTERVAL '1 second'
                        ) > rs.start_time
                )
                THEN TRUE

                ELSE FALSE
            END AS is_neutralised

        FROM laps l

        LEFT JOIN drivers d
            ON l.session_key = d.session_key
            AND l.driver_number = d.driver_number

        LEFT JOIN stints s
            ON l.session_key = s.session_key
            AND l.driver_number = s.driver_number
            AND l.lap_number
                BETWEEN s.lap_start AND s.lap_end

        LEFT JOIN pit_stops p
            ON l.session_key = p.session_key
            AND l.driver_number = p.driver_number
            AND l.lap_number = p.lap_number

        ASOF LEFT JOIN openf1_weather w
            ON l.session_key = w.session_key
            AND l.date_start >= w.date
    )

    SELECT
        *,

        CASE
            WHEN valid_for_pace = TRUE
                AND valid_weather_match = TRUE
                AND is_pit_stop = FALSE
                AND COALESCE(
                    is_pit_out_lap,
                    FALSE
                ) = FALSE
                AND is_neutralised = FALSE
            THEN TRUE

            ELSE FALSE
        END AS valid_green_flag_pace

    FROM lap_base;
""")

print("Created: lap_analysis")


# --------------------------------------------------
# Validate analytical model
# --------------------------------------------------

validation = conn.execute("""
    SELECT

        COUNT(*) AS total_rows,

        COUNT(
            DISTINCT
            CAST(session_key AS VARCHAR)
            || '-'
            || CAST(driver_number AS VARCHAR)
            || '-'
            || CAST(lap_number AS VARCHAR)
        ) AS unique_laps,

        COUNT(*) FILTER (
            WHERE valid_for_pace = TRUE
        ) AS valid_pace_laps,

        COUNT(*) FILTER (
            WHERE valid_for_strategy = TRUE
        ) AS valid_strategy_laps,

        COUNT(*) FILTER (
            WHERE valid_weather_match = TRUE
        ) AS valid_weather_laps,

        COUNT(*) FILTER (
            WHERE is_pit_stop = TRUE
        ) AS pit_stop_laps,

        COUNT(*) FILTER (
            WHERE is_neutralised = TRUE
        ) AS neutralised_laps,

        COUNT(*) FILTER (
            WHERE is_neutralised = FALSE
        ) AS non_neutralised_laps,

        COUNT(*) FILTER (
            WHERE is_neutralised IS NULL
        ) AS unknown_neutralisation_laps,

        COUNT(*) FILTER (
            WHERE valid_green_flag_pace = TRUE
        ) AS valid_green_flag_pace_laps

    FROM lap_analysis;
""").fetchdf()


print("\nValidation:")
print(validation.to_string(index=False))


# --------------------------------------------------
# Grain validation
# --------------------------------------------------

duplicate_laps = conn.execute("""
    SELECT
        session_key,
        driver_number,
        lap_number,
        COUNT(*) AS row_count

    FROM lap_analysis

    GROUP BY
        session_key,
        driver_number,
        lap_number

    HAVING COUNT(*) > 1;
""").fetchdf()


if len(duplicate_laps) > 0:

    print("\nWARNING: Duplicate driver-laps found:")
    print(duplicate_laps.to_string(index=False))

    raise ValueError(
        "lap_analysis grain validation failed"
    )

else:

    print(
        "\nGrain validation passed: "
        "one row per driver-lap"
    )


# --------------------------------------------------
# Validate green-flag analytical sample
# --------------------------------------------------

green_flag_validation = conn.execute("""
    SELECT
        rainfall,

        COUNT(*) AS lap_count,

        ROUND(
            MEDIAN(lap_duration),
            3
        ) AS median_lap_time

    FROM lap_analysis

    WHERE valid_green_flag_pace = TRUE

    GROUP BY rainfall

    ORDER BY rainfall;
""").fetchdf()


print("\nGreen-flag pace validation:")
print(green_flag_validation.to_string(index=False))


# --------------------------------------------------
# Close database connection
# --------------------------------------------------

conn.close()

print("\nDuckDB warehouse build complete")