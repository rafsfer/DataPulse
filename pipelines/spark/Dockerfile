FROM python:3.12-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends openjdk-17-jdk-headless && rm -rf /var/lib/apt/lists/*
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 PYTHONPATH=/workspace:/workspace/backend SPARK_LOCAL_IP=127.0.0.1
WORKDIR /workspace
COPY backend ./backend
COPY pipelines ./pipelines
COPY scripts ./scripts
COPY database ./database
COPY scala ./scala
RUN pip install --no-cache-dir "./backend[dev]" pyspark==3.5.4
RUN mkdir -p scala/target/classes && java -cp '/usr/local/lib/python3.12/site-packages/pyspark/jars/*' scala.tools.nsc.Main -usejavacp -d scala/target/classes scala/src/main/scala/SalesAggregation.scala scala/src/test/scala/SalesAggregationTest.scala && jar cf scala/target/datapulse.jar -C scala/target/classes .
ENV SCALA_JAR=/workspace/scala/target/datapulse.jar PIPELINE_ENGINE=spark
CMD ["python", "-m", "pipelines.runner"]
