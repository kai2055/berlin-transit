-- Average delay per line and station, with trip counts
-- Built on top of stg_departures

WITH delay_stats AS(
    SELECT
        line,
        station_name,
        EXTRACT(HOUR FROM planned_when) AS hour_of_day,

        AVG(delay_seconds) AS avg_delay_seconds,
        COUNT(*) AS trip_count,
        MAX(delay_seconds) AS max_delay_seconds,
        MIN(delay_seconds) AS min_delay_seconds

    FROM {{ ref('stg_departures') }}

    WHERE delay_seconds IS NOT NULL
    GROUP BY line, station_name, EXTRACT(HOUR FROM planned_when)
)

SELECT * FROM delay_stats
ORDER BY avg_delay_seconds DESC 
