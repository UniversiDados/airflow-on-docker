# scripts/04_enrich_countries_data.py
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
import argparse

def enrich_data(spark, processed_countries_path, economic_data_path, output_path_delta):
    """
    Faz o join dos dados de países processados com dados econômicos.
    Salva o resultado em formato Delta.
    """
    print(f"Lendo dados processados de países de: {processed_countries_path}")
    df_countries = spark.read.format("delta").load(processed_countries_path)

    print(f"Lendo dados econômicos de: {economic_data_path}")
    df_economic = spark.read.format("delta").load(economic_data_path)

    print("Realizando Left Join para enriquecer os dados dos países...")
    # Usar broadcast no DataFrame menor (df_economic) [cite: 527, 546]
    df_enriched = df_countries.join(
        F.broadcast(df_economic),
        df_countries["country_code_3"] == df_economic["country_code_3_econ"],
        "left"
    ).drop("country_code_3_econ") # Remove a coluna duplicada da chave de join [cite: 510]
    
    print("Schema do DataFrame enriquecido:")
    df_enriched.printSchema()

    # Tratar nulos introduzidos pelo left join [cite: 560]
    df_enriched = df_enriched.fillna({
        "gdp_per_capita": 0, # Ou outra estratégia, como média regional se disponível
        "hdi": 0.0           # Ou outra estratégia
    })

    print(f"Salvando DataFrame enriquecido em Delta: {output_path_delta}")
    df_enriched.write.format("delta").mode("overwrite").save(output_path_delta)
    print("DataFrame enriquecido salvo com sucesso.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enriquece dados de países com dados econômicos.")
    parser.add_argument("--processed_countries_path", required=True, help="Caminho da tabela Delta de países processados.")
    parser.add_argument("--economic_data_path", required=True, help="Caminho da tabela Delta de dados econômicos.")
    parser.add_argument("--output_path_delta", required=True, help="Caminho para salvar a tabela Delta enriquecida.")
    
    args = parser.parse_args()

    spark = SparkSession.builder.appName("EnrichCountriesData").getOrCreate()
    
    enrich_data(spark, args.processed_countries_path, args.economic_data_path, args.output_path_delta)
    
    spark.stop()