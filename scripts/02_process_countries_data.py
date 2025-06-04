# scripts/02_process_countries_data.py
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType, ArrayType, LongType,
    DoubleType, MapType, BooleanType
)
import argparse

def process_data(spark, input_path, output_path_delta):
    """
    Lê dados JSON brutos, aplica schema, achata e calcula densidade populacional.
    Salva o resultado em formato Delta.
    """
    print(f"Iniciando processamento do arquivo: {input_path}")

    # Schema abrangente baseado no explorado nas aulas [cite: 238, 373]
    # (Simplificado para os campos mais relevantes para a prática)
    car_schema = StructType([
        StructField("signs", ArrayType(StringType(), True), True),
        StructField("side", StringType(), True)
    ])

    country_schema = StructType([
        StructField("name", StructType([
            StructField("common", StringType(), True),
            StructField("official", StringType(), True),
        ]), True),
        StructField("cca2", StringType(), True),
        StructField("cca3", StringType(), True),
        StructField("status", StringType(), True),
        StructField("unMember", BooleanType(), True),
        StructField("currencies", MapType(StringType(), StructType([
            StructField("name", StringType(), True),
            StructField("symbol", StringType(), True)
        ])), True),
        StructField("capital", ArrayType(StringType(), True), True),
        StructField("region", StringType(), True),
        StructField("subregion", StringType(), True),
        StructField("languages", MapType(StringType(), StringType()), True),
        StructField("latlng", ArrayType(DoubleType(), True), True),
        StructField("landlocked", BooleanType(), True),
        StructField("area", DoubleType(), True),
        StructField("population", LongType(), True),
        StructField("continents", ArrayType(StringType(), True), True),
        StructField("car", car_schema, True),
        StructField("timezones", ArrayType(StringType(), True), True)
    ])

    raw_df = spark.read.json(input_path, schema=country_schema, multiLine=True)
    print("Schema aplicado ao DataFrame bruto:")
    raw_df.printSchema()

    flattened_df = raw_df.select(
        F.col("name.common").alias("common_name"),
        F.col("name.official").alias("official_name"),
        F.col("cca3").alias("country_code_3"),
        F.col("region"),
        F.col("subregion"),
        F.when(
            F.col("capital").isNotNull() & (F.size(F.col("capital")) > 0),
            F.col("capital").getItem(0)
        ).otherwise(None).alias("capital_city"),
        F.col("population"),
        F.col("area"),
        F.when(
            F.col("currencies").isNotNull() & (F.size(F.map_keys(F.col("currencies"))) > 0),
            F.map_keys(F.col("currencies")).getItem(0)
        ).otherwise(None).alias("currency_code"),
        F.when(
            F.col("currencies").isNotNull() & (F.size(F.map_values(F.col("currencies"))) > 0),
            F.map_values(F.col("currencies")).getItem(0).getField("name")
        ).otherwise(None).alias("currency_name"),
        F.col("languages"),
        F.col("unMember")
    )
    print("Schema do DataFrame achatado:")
    flattened_df.printSchema()

    # Calcular densidade populacional [cite: 258, 393]
    df_with_density = flattened_df.withColumn(
        "population_density",
        F.when(F.col("area").isNotNull() & (F.col("area") > 0), F.col("population") / F.col("area"))
         .otherwise(None)
    )
    print("Schema após adicionar densidade populacional:")
    df_with_density.printSchema()

    print(f"Salvando DataFrame processado em Delta: {output_path_delta}")
    df_with_density.write.format("delta").mode("overwrite").save(output_path_delta)
    print("DataFrame processado salvo com sucesso.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Processa dados de países em JSON para Delta.")
    parser.add_argument("--input_path", required=True, help="Caminho do arquivo JSON de entrada.")
    parser.add_argument("--output_path_delta", required=True, help="Caminho para salvar a tabela Delta de saída.")

    args = parser.parse_args()

    spark = SparkSession.builder.appName("ProcessCountriesData").getOrCreate()
    
    process_data(spark, args.input_path, args.output_path_delta)
    
    spark.stop()