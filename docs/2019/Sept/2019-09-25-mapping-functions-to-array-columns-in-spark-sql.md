# Mapping a function on a Array Column Element in Spark.SQL

Scala is great for mapping a function to a sequence of items, and works straightforwardly
for Arrays, Lists, Sequences, etc..

It is a little more cumbersome to map a function to theses types of data structures
if they are a column within a DataFrame.
The (minor) unpleasantness that you encounter include:
* Array elements are wrapped as **WrappedArray** types, and
* There is no (apparent) way to use the column expressions to simply assign a new
column expression.

As an example, lets create a simple example Data Frame:
```scala
scala> val df = Seq((Array("cat", "hippo", "elephant"), 3),(Array("bird", "bat", "tiger"),4)).toDF("column1", "column2")
df: org.apache.spark.sql.DataFrame = [column1: array<string>, column2: int]

scala> df.show()
+--------------------+-------+
|             column1|column2|
+--------------------+-------+
|[cat, hippo, elep...|      3|
|  [bird, bat, tiger]|      4|
+--------------------+-------+
```
For the sake of argument, let's say we want to create a new column that contains the array of **Long** values of the corresponding string lengths of elements in column1.

What we would like to be able to say is something like:
```scala
val df2 = df.withColumn("strlens", $"column1".map(x => x.length))
```
but to my knowledge this type of functionality is not available.

To make things easier, I would like to make a User Defined Function factory (where "UserDefinedFunction" is the Spark.SQL function that can be applied to column data fields) that takes as an argument a function to be applied to each element of the sequence

```scala
def mapStringToLongToStringArrayUdf(func : String => Long) : UserDefinedFunction = {

    val mapFunc : ((String => Long), WrappedArray[String]) =>
     WrappedArray[Long] = (fn : (String => Long), elems: WrappedArray[String]) => {
        elems.toIterator.map(x => fn(x)).toArray
    }
    val theArrayType = createArrayType(LongType)
    val udfFunc : WrappedArray[String] => WrappedArray[Long] =
      (input : WrappedArray[String]) => {
        val r : WrappedArray[Long] = mapFunc(func,input)
        r
    }
    udf(udfFunc,theArrayType)
}
```
The simple function to be applied is trivial, and we construct a UDF from the above function as:
```scala
val slen : String => Long = (x : String) => x.length
val slenUDF = mapStringToLongToStringArrayUdf(slen)
```
Now it is easy to create the desired column using this UDF:
```scala
df.withColumn("strlen(col1)", slenUDF($"column1")).show()
```
giving the output:
```
+--------------------+-------+------------+
|             column1|column2|strlen(col1)|
+--------------------+-------+------------+
|[cat, hippo, elep...|      3|   [3, 5, 8]|
|  [bird, bat, tiger]|      4|   [4, 3, 5]|
+--------------------+-------+------------+
```
If I had more time, I would make the above more generic, taking a function with parameters specifying the input- and output-types.

[Home](../../README.md)
