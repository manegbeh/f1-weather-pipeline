import duckdb


# -----------------------------
# Connect to DuckDB
# -----------------------------

database_path = "data/warehouse/f1_weather.duckdb"

conn = duckdb.connect(database_path)


# -----------------------------
# Tyre compound usage
# -----------------------------

compound_usage = conn.execute("""
    SELECT
        compound,
        COUNT(*) AS driver_laps

    FROM lap_analysis

    WHERE valid_for_strategy = TRUE

    GROUP BY compound

    ORDER BY driver_laps DESC;
""").fetchdf()


print("\nTyre compound usage:")
print(compound_usage.to_string(index=False))

# -----------------------------
# Wet tyre usage by driver
# -----------------------------

wet_tyre_usage = conn.execute("""
    SELECT
        full_name,
        driver_number,
        stint_number,
        MIN(lap_number) AS first_lap,
        MAX(lap_number) AS last_lap,
        COUNT(*) AS driver_laps,
        ROUND(AVG(rainfall), 2) AS rainfall_rate,
        ROUND(AVG(track_temperature), 2) AS avg_track_temperature,
        ROUND(AVG(humidity), 2) AS avg_humidity

    FROM lap_analysis

    WHERE valid_for_strategy = TRUE
        AND compound = 'WET'
        AND valid_weather_match = TRUE

    GROUP BY
        full_name,
        driver_number,
        stint_number

    ORDER BY
        first_lap,
        driver_number;
""").fetchdf()


print("\nWet tyre usage:")
print(wet_tyre_usage.to_string(index=False))

# -----------------------------
# Tyre strategy by stint
# -----------------------------

tyre_strategy = conn.execute("""
    SELECT
        full_name,
        driver_number,
        stint_number,
        compound,
        MIN(lap_number) AS first_lap,
        MAX(lap_number) AS last_lap,
        COUNT(*) AS driver_laps

    FROM lap_analysis

    WHERE valid_for_strategy = TRUE

    GROUP BY
        full_name,
        driver_number,
        stint_number,
        compound

    ORDER BY
        driver_number,
        stint_number;
""").fetchdf()


print("\nTyre strategy by stint:")
print(tyre_strategy.to_string(index=False))

# -----------------------------
# Close connection
# -----------------------------

conn.close()