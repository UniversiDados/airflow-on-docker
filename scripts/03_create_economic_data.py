# scripts/03_create_economic_data.py
from pyspark.sql import SparkSession
import argparse

def create_simulated_data(spark, output_path_delta):
    """
    Cria um DataFrame simulado com dados econômicos e salva em formato Delta.
    """
    print("Criando DataFrame econômico simulado.")
    economic_data = [
        ("USA", 65000, 0.926), ("CHN", 10500, 0.761), ("JPN", 40000, 0.919),
        ("DEU", 46000, 0.947), ("IND", 2100, 0.645), ("GBR", 42000, 0.932),
        ("FRA", 41000, 0.901), ("BRA", 7500, 0.765), ("ITA", 34000, 0.892),
        ("CAN", 46000, 0.929), ("KOR", 31000, 0.916), ("RUS", 11500, 0.824),
        ("AUS", 55000, 0.944), ("ESP", 29000, 0.904), ("MEX", 9900, 0.779),
        ("IDN", 4100, 0.718), ("NGA", 2200, 0.539), ("ZAF", 6000, 0.709), # South Africa
        ("EGY", 3500, 0.707), # Egypt
        ("ARG", 9900, 0.845)  # Argentina
    ]
    economic_columns = ["country_code_3_econ", "gdp_per_capita", "hdi"] [cite: 516]
    
    df_economic = spark.createDataFrame(economic_data, economic_columns)
    print("Schema do DataFrame econômico:")
    df_economic.printSchema()
    
    print(f"Salvando DataFrame econômico em Delta: {output_path_delta}")
    df_economic.write.format("delta").mode("overwrite").save(output_path_delta)
    print("DataFrame econômico salvo com sucesso.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cria dados econômicos simulados e salva em Delta.")
    parser.add_argument("--output_path_delta", required=True, help="Caminho para salvar a tabela Delta de saída.")
    
    args = parser.parse_args()

    spark = SparkSession.builder.appName("CreateEconomicData").getOrCreate()
    
    create_simulated_data(spark, args.output_path_delta)
    
    spark.stop()