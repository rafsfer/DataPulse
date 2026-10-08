"""DataFrame transformations executed by Spark, with bounded local serving export."""

from pyspark.sql import SparkSession, functions as F
from pyspark.sql.types import IntegerType, StringType, StructField, StructType


def transform(valid, customers, products):
    spark = (
        SparkSession.builder.master("local[2]")
        .appName("DataPulse")
        .config("spark.sql.shuffle.partitions", "2")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )
    try:
        schema = StructType(
            [
                StructField(key, IntegerType() if key == "quantity" else StringType())
                for key in [
                    "order_id",
                    "customer_id",
                    "product_id",
                    "quantity",
                    "amount",
                    "ordered_at",
                ]
            ]
        )
        orders = spark.createDataFrame(valid, schema=schema).dropDuplicates(
            ["order_id"]
        )
        orders = orders.select(
            *[
                F.trim(F.col(c)).alias(c) if c != "quantity" else F.col(c)
                for c in orders.columns
            ]
        ).withColumn("amount", F.col("amount").cast("decimal(16,2)"))
        customer_frame = spark.createDataFrame(
            customers, "customer_id string, region string"
        )
        product_frame = spark.createDataFrame(
            products, "product_id string, category string"
        )
        silver = orders.join(customer_frame, "customer_id", "inner").join(
            product_frame, "product_id", "inner"
        )
        gold = silver.groupBy("region", "category").agg(
            F.sum("amount").alias("revenue"),
            F.count("order_id").alias("orders"),
            F.sum("quantity").alias("units"),
        )
        return silver.toPandas(), gold.toPandas()
    finally:
        spark.stop()
