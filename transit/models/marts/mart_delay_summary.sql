-- Average delay per line, station, and hour (Berlin local time),
-- built on the deduplicated final delays.


WITH delay_stats AS (
    SELECT
        line,
        station_name,
        EXTRACT(HOUR FROM planned_when AT TIME ZONE 'Europe/Berlin') AS hour_of_day,
        AVG(delay_seconds) AS avg_delay_seconds,
        COUNT(*)           AS trip_count,
        MAX(delay_seconds) AS max_delay_seconds,
        MIN(delay_seconds) AS min_delay_seconds
    FROM {{ ref('int_departures_latest') }}
    WHERE delay_seconds IS NOT NULL
    GROUP BY line, station_name,
            EXTRACT(HOUR FROM planned_when AT TIME ZONE 'Europe/Berlin')
)

SELECT * FROM delay_stats
ORDER BY avg_delay_seconds DESC
