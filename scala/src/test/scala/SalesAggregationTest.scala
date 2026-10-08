import org.apache.spark.sql.SparkSession
object SalesAggregationTest {
  def main(args: Array[String]): Unit = {
    val spark = SparkSession.builder().master("local[2]").appName("Scala aggregation test").getOrCreate()
    import spark.implicits._
    try {
      val source = Seq(("O1","South","Tech",2,10.50), ("O2","South","Tech",1,20.25))
        .toDF("order_id","region","category","quantity","amount")
      val result = SalesAggregation.aggregate(source).collect()
      assert(result.length == 1)
      assert(result(0).getAs[Long]("orders") == 2)
      assert(result(0).getAs[Long]("units") == 3)
      assert(result(0).getAs[java.math.BigDecimal]("revenue").toPlainString == "30.75")
      println("Scala aggregation assertions passed")
    } finally { spark.stop() }
  }
}
