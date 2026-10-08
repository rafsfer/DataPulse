import org.apache.spark.sql.{DataFrame, SparkSession}
import org.apache.spark.sql.functions._

object SalesAggregation {
  def aggregate(sales: DataFrame): DataFrame = {
    sales.groupBy("region", "category").agg(
      sum(col("amount").cast("decimal(16,2)")).alias("revenue"),
      count(col("order_id")).alias("orders"),
      sum(col("quantity")).alias("units")
    )
  }
  def main(args: Array[String]): Unit = {
    require(args.length == 2, "Usage: SalesAggregation SILVER_PATH GOLD_PATH")
    val spark = SparkSession.builder().appName("DataPulse Scala regional sales").getOrCreate()
    try {
      aggregate(spark.read.parquet(args(0))).write.mode("overwrite").parquet(args(1))
    } finally { spark.stop() }
  }
}
