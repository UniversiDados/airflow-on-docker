# dags/dag_paises_pipeline.py
from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
import os

# Define o diretório base para os dados. No Docker, este caminho deve ser acessível pelo Airflow e Spark.
# Se estiver usando volumes Docker, ajuste conforme necessário.
BASE_DATA_PATH = "/opt/airflow/data/delta" # Caminho dentro do container Airflow
# BASE_DATA_PATH_HOST = "./data/delta" # Caminho no host, se mapeado para o de cima

# Garante que os diretórios base existam no worker/scheduler Airflow (para o PythonOperator)
# Para SparkSubmitOperator, o Spark se encarrega de criar no HDFS/local se não existir.
# No entanto, para caminhos locais, é bom garantir no script Python.
# Os scripts PySpark já contêm os.makedirs() para os output_paths.

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

    # Caminhos para os scripts e dados
    # Ajuste o caminho para os scripts se o seu diretório de DAGs não for a raiz do projeto
    scripts_path = "/opt/airflow/scripts" # Caminho dentro do container Airflow

    raw_json_path = os.path.join(BASE_DATA_PATH, "raw_countries", "countries.json")
    processed_countries_delta_path = os.path.join(BASE_DATA_PATH, "processed_countries")
    economic_data_delta_path = os.path.join(BASE_DATA_PATH, "economic_data")
    enriched_countries_delta_path = os.path.join(BASE_DATA_PATH, "enriched_countries")
    regional_stats_delta_path = os.path.join(BASE_DATA_PATH, "regional_stats")
    final_report_delta_path = os.path.join(BASE_DATA_PATH, "final_countries_report")

    extract_api_data = PythonOperator(
        task_id='extract_api_data',
        python_callable=lambda: os.system(f"python {scripts_path}/01_extract_api_data.py --output_path {raw_json_path}"),
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
        application=f'{scripts_path}/03_create_economic_data.py',
        conn_id='spark_default', # Ajuste se necessário
        application_args=[
            '--output_path_delta', economic_data_delta_path
        ],
        doc_md="""
        #### Tarefa de Criação de Dados Econômicos
        Executa o script PySpark `03_create_economic_data.py`.
        Cria um DataFrame simulado com dados econômicos (PIB per capita, IDH)
        e salva em formato Delta Lake.
        """
    )

    enrich_countries_data = SparkSubmitOperator(
        task_id='enrich_countries_data',
        application=f'{scripts_path}/04_enrich_countries_data.py',
        conn_id='spark_default', # Ajuste se necessário
        application_args=[
            '--processed_countries_path', processed_countries_delta_path,
            '--economic_data_path', economic_data_delta_path,
            '--output_path_delta', enriched_countries_delta_path
        ],
        doc_md="""
        #### Tarefa de Enriquecimento de Dados
        Executa o script PySpark `04_enrich_countries_data.py`.
        Faz o join dos dados de países processados com os dados econômicos simulados
        e salva o resultado em formato Delta Lake.
        """
    )

    aggregate_regional_stats = SparkSubmitOperator(
        task_id='aggregate_regional_stats',
        application=f'{scripts_path}/05_aggregate_regional_stats.py',
        conn_id='spark_default', # Ajuste se necessário
        application_args=[
            '--enriched_countries_path', enriched_countries_delta_path,
            '--output_path_delta', regional_stats_delta_path
        ],
        doc_md="""
        #### Tarefa de Agregação de Estatísticas Regionais
        Executa o script PySpark `05_aggregate_regional_stats.py`.
        Agrega os dados enriquecidos para calcular estatísticas médias (IDH, PIB, densidade) por região
        e salva o resultado em formato Delta Lake.
        """
    )

    load_final_data = SparkSubmitOperator(
        task_id='load_final_data',
        application=f'{scripts_path}/06_load_final_data.py',
        conn_id='spark_default', # Ajuste se necessário
        application_args=[
            '--enriched_countries_path', enriched_countries_delta_path,
            '--final_report_path_delta', final_report_delta_path
        ],
        doc_md="""
        #### Tarefa de Carga Final
        Executa o script PySpark `06_load_final_data.py`.
        Simula a carga dos dados enriquecidos de países para uma tabela final de 'relatório',
        salvando em formato Delta Lake.
        """
    )

    # Definindo as dependências
    extract_api_data >> process_countries_data
    process_countries_data >> enrich_countries_data
    create_economic_data >> enrich_countries_data
    enrich_countries_data >> aggregate_regional_stats
    enrich_countries_data >> load_final_data