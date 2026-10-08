# Optional distributed processing and orchestration

Spark 3.5.4 is pinned with Java 17 and Scala 2.12.18. The compiler is taken from
Spark's own jars so the demo can build without another sbt runtime. build.sbt is
provided for standard IDE builds. Scala owns one regional/category aggregation,
not the Python validation engine.

```bash
docker compose --profile advanced build spark
docker compose --profile advanced run --rm spark python -m pipelines.ingestion.generator --output data/generated/demo --volume 1000
docker compose --profile advanced run --rm spark python -m pipelines.runner --source data/generated/demo --as-of 2026-10-07T12:00:00+00:00
docker compose --profile advanced run --rm spark pytest -q pipelines/tests/test_spark.py
docker compose --profile advanced run --rm spark spark-submit --master local[2] --class SalesAggregationTest scala/target/datapulse.jar
```

The generator and runner commands above require the same persisted source path;
use /workspace/backend/data/generated/demo for both commands when running separate
containers (the pipeline_data volume is mounted there). The default API uses
Pandas. The Spark profile explicitly selects PIPELINE_ENGINE=spark and SCALA_JAR.
Spark exports at most 100k rows to the local serving process in this portfolio;
this is not a claim of cluster-scale database loading. Scala writes a separate
Gold output within the same attempt and failures prevent PostgreSQL publication.

```bash
docker compose --profile orchestration up -d airflow
docker compose exec airflow airflow dags list-import-errors
docker compose exec airflow airflow dags test datapulse_commerce 2026-10-07
```

Airflow is a real scheduled DAG with retries, timeouts, dependency ordering and
max_active_runs=1. The backend retains its independent PostgreSQL run lock.
The DAG currently groups ingestion, validation and Silver/Gold publication in
one atomic backend task. Splitting these into independently resumable Airflow
tasks remains pending. Airflow standalone uses SQLite for its own local metadata;
application data remains PostgreSQL. Obtain the standalone password from its
local generated password file; do not publish it.

At least 4 GiB Docker memory is recommended by the Airflow Docker documentation;
this session reported approximately 1.8 GiB. Run optional profiles sequentially,
or increase Docker/WSL memory before combining them.

References: [Spark build compatibility](https://dlcdn.apache.org/spark/docs/3.5.4/building-spark.html)
and [Airflow Docker setup](https://airflow.apache.org/docs/apache-airflow/2.10.0/howto/docker-compose/index.html).
