# scripts/06_load_final_data.py
from pyspark.sql import SparkSession
import argparse

def load_final_report(spark, enriched_countries_path, final_report_path_delta):
    """
    Simula o carregamento final dos dados enriquecidos para um 'relatório' final.
    Na prática, poderia ser uma tabela de BI, etc.
    """
    print(f"Lendo dados enriquecidos de países de: {enriched_countries_path} para carga final.")
    df_final_report = spark.read.format("delta").load(enriched_countries_path)

    print("Schema do relatório final (dados enriquecidos de países):")
    df_final_report.printSchema()
    df_final_report.show(10, truncate=False)
    
    print(f"Salvando relatório final em Delta: {final_report_path_delta}")
    df_final_report.write.format("delta").mode("overwrite").save(final_report_path_delta)
    print("Relatório final salvo com sucesso.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Carrega os dados finais de países para um 'relatório'.")
    parser.add_argument("--enriched_countries_path", required=True, help="Caminho da tabela Delta de países enriquecidos.")
    parser.add_argument("--final_report_path_delta", required=True, help="Caminho para salvar a tabela Delta do relatório final.")
    
    args = parser.parse_args()

    spark = SparkSession.builder.appName("LoadFinalReport").getOrCreate()
    
    load_final_report(spark, args.enriched_countries_path, args.final_report_path_delta)
    
    spark.stop()