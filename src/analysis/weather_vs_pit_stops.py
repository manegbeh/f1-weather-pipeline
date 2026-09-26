import duckdb


# -----------------------------
# Connect to DuckDB
# -----------------------------

database_path = "data/warehouse/f1_weather.duckdb"

conn = duckdb.connect(database_path)


# -----------------------------
# Pit stops throughout the race
# -----------------------------

pit_stops = conn.execute("""
    SELECT
        full_name,
        driver_number,
        lap_number,
        compound,
        rainfall,
        air_temperature,
        track_temperature,
        humidity,
        is_neutralised,
        pit_duration,
        lane_duration,
        stop_duration

    FROM lap_analysis

    WHERE is_pit_stop = TRUE

    ORDER BY
        lap_number,
        driver_number;
""").fetchdf()


print("\nPit stops:")
print(pit_stops.to_string(index=False))


# -----------------------------
# Pit stops by lap
# -----------------------------

pit_stops_by_lap = conn.execute("""
    SELECT
        lap_number,
        COUNT(*) AS pit_stops,
        rainfall,

        ROUND(
            AVG(track_temperature),
            2
        ) AS avg_track_temperature,

        ROUND(
            AVG(humidity),
            2
        ) AS avg_humidity

    FROM lap_analysis

    WHERE is_pit_stop = TRUE
        AND valid_weather_match = TRUE

    GROUP BY
        lap_number,
        rainfall

    ORDER BY
        lap_number,
        rainfall;
""").fetchdf()


print("\nPit stops by lap:")
print(pit_stops_by_lap.to_string(index=False))


# -----------------------------
# Pit stops by rainfall
# -----------------------------

pit_stops_by_rainfall = conn.execute("""
    SELECT
        rainfall,
        COUNT(*) AS pit_stops

    FROM lap_analysis

    WHERE is_pit_stop = TRUE
        AND valid_weather_match = TRUE

    GROUP BY rainfall

    ORDER BY rainfall;
""").fetchdf()


print("\nPit stops by rainfall:")
print(pit_stops_by_rainfall.to_string(index=False))

# -----------------------------
# Tyre changes at pit stops
# -----------------------------

tyre_changes = conn.execute("""
    WITH pit_events AS (
        SELECT
            p.full_name,
            p.driver_number,
            p.lap_number AS pit_lap,
            p.compound AS old_compound,
            p.rainfall,
            p.is_neutralised,

            next_lap.compound AS new_compound

        FROM lap_analysis p

        LEFT JOIN lap_analysis next_lap
            ON p.session_key = next_lap.session_key
            AND p.driver_number = next_lap.driver_number
            AND next_lap.lap_number = p.lap_number + 1

        WHERE p.is_pit_stop = TRUE
    )

    SELECT
        full_name,
        driver_number,
        pit_lap,
        old_compound,
        new_compound,
        rainfall,
        is_neutralised,

        CASE
            WHEN new_compound IS NULL
                THEN 'UNKNOWN'

            WHEN old_compound = new_compound
                THEN 'SAME COMPOUND'

            ELSE 'COMPOUND CHANGE'
        END AS change_type

    FROM pit_events

    ORDER BY
        pit_lap,
        driver_number;
""").fetchdf()


print("\nTyre changes at pit stops:")
print(tyre_changes.to_string(index=False))

# -----------------------------
# Close connection
# -----------------------------

conn.close()