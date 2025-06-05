# dags/dag_paises_pipeline.py
from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
import os
import sys
import importlib.util
import subprocess

BASE_DATA_PATH = "/opt/airflow/data/delta" # Caminho dentro do container Airflow

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
}

with DAG(
    dag_id='pipeline_dados_paises',
    default_args=default_args,
    schedule_interval=None,
    start_date=days_ago(1),
    catchup=False,
    tags=['pyspark', 'restcountries', 'delta_lake'],
    doc_md="""
    ### Pipeline de Dados de Países
    Este pipeline ETL extrai dados da API REST Countries, processa com PySpark e armazena em Delta Lake.
    - **Extração**: Coleta dados JSON da API.
    - **Processamento**: Transforma JSON em tabela Delta, calcula densidade populacional.
    - **Criação Dados Econômicos**: Gera um DataFrame simulado com dados econômicos.
    - **Enriquecimento**: Junta dados de países com dados econômicos.
    - **Agregação**: Calcula estatísticas regionais.
    - **Carga Final**: Salva o DataFrame enriquecido como um 'relatório' final.
    """
) as dag:
    scripts_path = "/opt/airflow/scripts" # Caminho dentro do container Airflow

    raw_json_path = os.path.join(BASE_DATA_PATH, "countries.json")
    processed_countries_delta_path = os.path.join(BASE_DATA_PATH, "processed_countries")
    economic_data_delta_path = os.path.join(BASE_DATA_PATH, "economic_data")
    enriched_countries_delta_path = os.path.join(BASE_DATA_PATH, "enriched_countries")
    regional_stats_delta_path = os.path.join(BASE_DATA_PATH, "regional_stats")
    final_report_delta_path = os.path.join(BASE_DATA_PATH, "final_countries_report")

    def extract_api_data_callable(output_path):
        """
        Python callable to run the extract_api_data script.
        """
        script_path = "/opt/airflow/scripts/01_extract_api_data.py"
        
        spec = importlib.util.spec_from_file_location("extract_api_data", script_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules["extract_api_data"] = module
        spec.loader.exec_module(module)
        
        module.extract_data("https://restcountries.com/v3.1/all", output_path)

    extract_api_data = PythonOperator(
        task_id='extract_api_data',
        python_callable=extract_api_data_callable,
        op_kwargs={'output_path': raw_json_path},
        doc_md="""
        #### Tarefa de Extração da API
        Executa o script Python `01_extract_api_data.py` para buscar dados da API REST Countries
        e salvar o resultado como um arquivo JSON bruto.
        """
    )
    
    # IMPORTANTE: Defina sua conexão Spark ou configure o spark-submit no seu ambiente
    # Se o spark-submit estiver no PATH e configurado (ex: SPARK_HOME), pode não precisar de `conn_id`.
    # Para um ambiente Docker local com Spark, `conn_id='spark_default'` é comum se configurada na UI do Airflow.
    # Para esta atividade local, assumimos que `spark-submit` está acessível e os paths são locais para o Spark.
    
    process_countries_data = SparkSubmitOperator(
        task_id='process_countries_data',
        application=f'{scripts_path}/02_process_countries_data.py',
        conn_id='spark_default', # Ajuste se necessário
        conf={
            'spark.jars.packages': 'io.delta:delta-core_2.12:2.4.0',
            'spark.sql.extensions': 'io.delta.sql.DeltaSparkSessionExtension',
            'spark.sql.catalog.spark_catalog': 'org.apache.spark.sql.delta.catalog.DeltaCatalog'
        },
        application_args=[
            '--input_path', raw_json_path,
            '--output_path_delta', processed_countries_delta_path
        ],
        doc_md="""
        #### Tarefa de Processamento de Dados de Países
        Executa o script PySpark `02_process_countries_data.py`.
        Lê o JSON bruto, aplica schema, achata a estrutura, calcula a densidade populacional
        e salva o resultado em formato Delta Lake.
        """
    )

    create_economic_data = SparkSubmitOperator(
        task_id='create_economic_data',
        application='/opt/airflow/scripts/03_create_economic_data.py',
        conn_id='spark_default',
        verbose=True,
        conf={
            'spark.jars.packages': 'io.delta:delta-core_2.12:2.4.0',
            'spark.sql.extensions': 'io.delta.sql.DeltaSparkSessionExtension',
            'spark.sql.catalog.spark_catalog': 'org.apache.spark.sql.delta.catalog.DeltaCatalog'
        },
        application_args=[
            '--country_codes_path', '/opt/airflow/data/country_codes.txt',
            '--output_path_delta', '/opt/airflow/data/delta/economic_data'
        ]
    )

    enrich_countries_data = SparkSubmitOperator(
        task_id='enrich_countries_data',
        application='/opt/airflow/scripts/04_enrich_countries_data.py',
        conn_id='spark_default',
        verbose=True,
        conf={
            'spark.jars.packages': 'io.delta:delta-core_2.12:2.4.0',
            'spark.sql.extensions': 'io.delta.sql.DeltaSparkSessionExtension',
            'spark.sql.catalog.spark_catalog': 'org.apache.spark.sql.delta.catalog.DeltaCatalog'
        },
        application_args=[
            '--countries_path', '/opt/airflow/data/delta/processed_countries',
            '--economic_path', '/opt/airflow/data/delta/economic_data',
            '--output_path', '/opt/airflow/data/delta/enriched_countries'
        ]
    )

    aggregate_regional_stats = SparkSubmitOperator(
        task_id='aggregate_regional_stats',
        application='/opt/airflow/scripts/05_aggregate_regional_stats.py',
        conn_id='spark_default',
        verbose=True,
        conf={
            'spark.jars.packages': 'io.delta:delta-core_2.12:2.4.0',
            'spark.sql.extensions': 'io.delta.sql.DeltaSparkSessionExtension',
            'spark.sql.catalog.spark_catalog': 'org.apache.spark.sql.delta.catalog.DeltaCatalog'
        },
        application_args=[
            '--input_path', '/opt/airflow/data/delta/enriched_countries',
            '--output_path', '/opt/airflow/data/delta/regional_stats'
        ]
    )

    load_final_data = SparkSubmitOperator(
        task_id='load_final_data',
        application=f'{scripts_path}/06_load_final_data.py',
        conn_id='spark_default',
        conf={
            'spark.jars.packages': 'io.delta:delta-core_2.12:2.4.0',
            'spark.sql.extensions': 'io.delta.sql.DeltaSparkSessionExtension',
            'spark.sql.catalog.spark_catalog': 'org.apache.spark.sql.delta.catalog.DeltaCatalog'
        },
        application_args=[
            '--enriched_countries_path', enriched_countries_delta_path,
            '--final_report_path_delta', final_report_delta_path
        ],
        doc_md="""
        #### Tarefa de Carga Final
        Executa o script PySpark `06_load_final_data.py`.
        Carrega os dados finais e salva em formato Delta Lake.
        """
    )

    # Definindo as dependências
    extract_api_data >> process_countries_data
    process_countries_data >> enrich_countries_data
    create_economic_data >> enrich_countries_data
    enrich_countries_data >> aggregate_regional_stats
    enrich_countries_data >> load_final_data