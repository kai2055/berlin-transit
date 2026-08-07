-- One row per trip per station: the LAST delay we observed before the train departed  (its final, realized delay)

SELECt *
FROM {{ ref('stg_departures') }}
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY trip_id, station_id
    ORDER BY fetched_at DESC
) = 1
