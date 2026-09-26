import duckdb


# -----------------------------
# Connect to DuckDB
# -----------------------------

database_path = "data/warehouse/f1_weather.duckdb"

conn = duckdb.connect(database_path)


# -----------------------------
# Rainfall vs lap pace
# Green-flag racing only
# -----------------------------

rainfall_pace = conn.execute("""
    SELECT
        rainfall,

        COUNT(*) AS lap_count,

        ROUND(
            AVG(lap_duration),
            3
        ) AS average_lap_time,

        ROUND(
            MEDIAN(lap_duration),
            3
        ) AS median_lap_time,

        ROUND(
            MIN(lap_duration),
            3
        ) AS fastest_lap,

        ROUND(
            MAX(lap_duration),
            3
        ) AS slowest_lap

    FROM lap_analysis

    WHERE valid_for_pace = TRUE
        AND valid_weather_match = TRUE
        AND is_pit_stop = FALSE
        AND is_pit_out_lap = FALSE
        AND is_neutralised = FALSE

    GROUP BY rainfall

    ORDER BY rainfall;
""").fetchdf()


print("\nGreen-flag pace by rainfall:")
print(rainfall_pace.to_string(index=False))


# -----------------------------
# Pace throughout the race
# Green-flag racing only
# -----------------------------

race_pace = conn.execute("""
    SELECT
        lap_number,
        rainfall,

        COUNT(*) AS driver_laps,

        ROUND(
            MEDIAN(lap_duration),
            3
        ) AS median_lap_time

    FROM lap_analysis

    WHERE valid_for_pace = TRUE
        AND valid_weather_match = TRUE
        AND is_pit_stop = FALSE
        AND is_pit_out_lap = FALSE
        AND is_neutralised = FALSE

    GROUP BY
        lap_number,
        rainfall

    ORDER BY
        lap_number,
        rainfall;
""").fetchdf()


print("\nGreen-flag race pace by lap and rainfall:")
print(race_pace.to_string(index=False))


# -----------------------------
# Weather changes during race
# -----------------------------

weather_changes = conn.execute("""
    WITH weather_states AS (
        SELECT
            weather_time,
            rainfall,

            LAG(rainfall) OVER (
                ORDER BY weather_time
            ) AS previous_rainfall

        FROM (
            SELECT DISTINCT
                weather_time,
                rainfall

            FROM lap_analysis

            WHERE valid_weather_match = TRUE
        )
    )

    SELECT
        weather_time,
        previous_rainfall,
        rainfall

    FROM weather_states

    WHERE previous_rainfall IS NULL
        OR rainfall != previous_rainfall

    ORDER BY weather_time;
""").fetchdf()


print("\nRainfall state changes:")
print(weather_changes.to_string(index=False))


# -----------------------------
# Investigate slower periods
# Green-flag racing only
# -----------------------------

slow_periods = conn.execute("""
    SELECT
        lap_number,

        ROUND(
            MEDIAN(lap_duration),
            3
        ) AS median_lap_time,

        ROUND(
            AVG(air_temperature),
            2
        ) AS air_temperature,

        ROUND(
            AVG(track_temperature),
            2
        ) AS track_temperature,

        ROUND(
            AVG(humidity),
            2
        ) AS humidity,

        ROUND(
            AVG(wind_speed),
            2
        ) AS wind_speed,

        rainfall,

        COUNT(*) AS driver_laps

    FROM lap_analysis

    WHERE valid_for_pace = TRUE
        AND valid_weather_match = TRUE
        AND is_pit_stop = FALSE
        AND is_pit_out_lap = FALSE
        AND is_neutralised = FALSE
        AND (
            lap_number BETWEEN 24 AND 35
            OR lap_number BETWEEN 37 AND 45
        )

    GROUP BY
        lap_number,
        rainfall

    ORDER BY
        lap_number,
        rainfall;
""").fetchdf()


print("\nWeather during selected green-flag race periods:")
print(slow_periods.to_string(index=False))


# -----------------------------
# Close connection
# -----------------------------

conn.close()