# scripts/05_aggregate_regional_stats.py
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
import argparse

def aggregate_stats(spark, enriched_countries_path, output_path_delta):
    """
    Agrega dados enriquecidos para calcular estatísticas por região.
    Salva o resultado em formato Delta.
    """
    print(f"Lendo dados enriquecidos de países de: {enriched_countries_path}")
    df_enriched = spark.read.format("delta").load(enriched_countries_path)

    print("Calculando estatísticas agregadas por região...")
    df_regional_stats = df_enriched.groupBy("region").agg(
        F.count("country_code_3").alias("num_countries"),
        F.sum("population").alias("total_population"),
        F.avg("area").alias("avg_area_sq_km"),
        F.avg("population_density").alias("avg_population_density"),
        F.avg("gdp_per_capita").alias("avg_gdp_per_capita"),
        F.avg("hdi").alias("avg_hdi")
    ).orderBy(F.col("avg_hdi").desc_nulls_last())
    
    print("Schema das estatísticas regionais:")
    df_regional_stats.printSchema()
    df_regional_stats.show(truncate=False)

    print(f"Salvando estatísticas regionais em Delta: {output_path_delta}")
    df_regional_stats.write.format("delta").mode("overwrite").save(output_path_delta)
    print("Estatísticas regionais salvas com sucesso.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agrega dados de países por região.")
    parser.add_argument("--enriched_countries_path", required=True, help="Caminho da tabela Delta de países enriquecidos.")
    parser.add_argument("--output_path_delta", required=True, help="Caminho para salvar a tabela Delta de estatísticas regionais.")
    
    args = parser.parse_args()

    spark = SparkSession.builder.appName("AggregateRegionalStats").getOrCreate()
    
    aggregate_stats(spark, args.enriched_countries_path, args.output_path_delta)
    
    spark.stop()