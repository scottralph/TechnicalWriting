# Sept. 11, 2019,  Case Classes for DataFrame Structured Columns

When defining a simple DataFrame schema, it is simple enough:
```scala
val schema = StructType (StructField("foo", StringType, true))
```

The problem I ran across is when I wanted a nested structure for one of the columns, and one of those entries had an array.
Additionally, I was constructing the data for the DataFrame by taking an existing DataFrame, accessing the RDD, and mapping it to a new nested structure.
"That's easy, I thought", and I just tried to author a nested structure:
```scala
val schema =  StructType(
  List(
    StructField("hlikey", StringType, true),
    StructField("states", ArrayType(
      StructType(Seq(
        StructField("statename", StringType, true),
        StructField("statetype", StringType, true),
        StructField("starttime", StringType, true),
        StructField("endtime", StringType, true)
      ))), true)
    )
  )
```
and then tie the schema to the DataFrame like:
```scala
val newRDD = inputDF.map(row => someFunction(row)).groupBy().reduce()... //Etc
val dataFrame = spark.createDataFrame(newRdd, schema)
```
The data from the RDD looked fine, but when I got to the **createDataFrame** it gave some opaque error about implicit conversion that gave very little insight into the how the mapping was failing.

## Solution
Again, I used the trusty friend the case class as described in [Fold Left Example](2019-09-05-fold-left.md)

```scala
case class StateEntry(stateName : String,
                      stateType : String,
                      startTime : String,
                      endTime : String)
case class HliStateEntry(hlikey : String, states : List[StateEntry])
```
The hierarchy is expressed as a simple parent-child relationship with a list.
The resulting function, is given below:
```scala
def collectStates(sparkSession : SparkSession) : DataFrame = {
  import sparkSession.implicits._
  val orderStatesTable = readOrderStatesTable()
  val rddHliStateEntry = orderStatesTable.select("hlikey",
    "statename", "statetype", "starttime", "endtime")
    .map(r => HliStateEntry(r.getString(0),
      List(StateEntry(r.getString(1), r.getString(2),
      r.getString(3), r.getString(4)))))
  val grouped = rddHliStateEntry.rdd.map(h => (h.hlikey, h))
    .groupByKey.map(r => (r._1, r._2.toList))
  val reducedGrouped : RDD[HliStateEntry] = grouped
    .map(pr => (pr._1, // make pair to keep hlikey
      pr._2.foldLeft(HliStateEntry(pr._1, List.empty[StateEntry]))
     ((acc,x) => HliStateEntry(x.hlikey, acc.states ++ x.states))))
    .map(_._2) // throw away hlikey (it's now in the case class)
  reducedGrouped.toDF()
}
```
The complex expressions in the function just massage the containment and grouping of the two case classes.
The only interesting things to note are:
* The import statement, that takes as input a *SparkSession*. This gives all the implicit type conversions to do all the case classes, lists, sequences, maps, etc.
* Ignoring the creational logic, the value **reducedGrouped** is an RDD of **HliStateEntry**. The schema is simply taken from the Case Class in the **toDF()** method.

```
scala> collectStates().printSchema
root
 |-- hlikey: string (nullable = true)
 |-- states: array (nullable = true)
 |    |-- element: struct (containsNull = true)
 |    |    |-- stateName: string (nullable = true)
 |    |    |-- stateType: string (nullable = true)
 |    |    |-- startTime: string (nullable = true)
 |    |    |-- endTime: string (nullable = true)
```

It is unfortunate that the method has to be passed an additional argument for the Spark Session, in order to import the implicit methods, but all that extra work someone did to get schema of nested structures can now be easily leveraged, and so it is worth the small aesthetic flaw.
