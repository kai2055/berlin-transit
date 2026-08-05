SELECT
  CAST(fetched_at AS TIMESTAMP)                        AS fetched_at,
  station_id,
  station_name,
  JSON_VALUE(dep, '$.line.name')                      AS line,
  JSON_VALUE(dep, '$.direction')                      AS direction,
  CAST(JSON_VALUE(dep, '$.plannedWhen') AS TIMESTAMP) AS planned_when,
  CAST(JSON_VALUE(dep, '$.when') AS TIMESTAMP)        AS actual_when,
  CAST(JSON_VALUE(dep, '$.delay') AS INT64)           AS delay_seconds,
  JSON_VALUE(dep, '$.tripId')                         AS trip_id
FROM {{ source('transit_raw', 'departures_raw') }},
UNNEST(JSON_QUERY_ARRAY(response, '$.departures')) AS dep