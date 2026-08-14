"""PySpark batch job: flatten raw VBB JSON from the lake into clean parquet."""

from pyspark.sql import SparkSession
from pyspark.sql.functions import explode, col

spark = SparkSession.builder.appName("flatten-departures").getOrCreate()

# Read every raw capture file (one JSON object per file)
raw = spark.read.json("/app/data")

# Exploding the departures array so each train becomes its own row
exploded = raw.select(
    col("fetched_at"),
    col("station_id"),
    col("station_name"),
    explode(col("response.departures")).alias("dep"),
)

# Pulling the fields we need from each departures
clean = exploded.select(
    col("fetched_at"),
    col("station_id"),
    col("station_name"),
    col("dep.line.name").alias("line"),
    col("dep.direction").alias("direction"),
    col("dep.plannedWhen").alias("planned_when"),
    col("dep.when").alias("actual_when"),
    col("dep.delay").alias("delay_seconds"),
    col("dep.tripId").alias("trip_id"),
)

clean.coalesce(1).write.mode("overwrite").parquet("/app/spark/output")
print(f"Wrote {clean.count()} rows to spark/output")

spark.stop()


