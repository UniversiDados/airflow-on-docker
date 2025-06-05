FROM apache/airflow:2.8.1

USER root

# Instalar Java (OpenJDK 17), wget e procps (para o comando ps)
RUN apt-get update && \
    apt-get install -y --no-install-recommends openjdk-17-jdk wget procps && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Verificar o caminho real da instalação do Java (opcional, mas útil para depuração)
RUN ls -l /usr/lib/jvm/

# Configurar variáveis de ambiente para Java e Spark
# AJUSTE O CAMINHO DO JAVA_HOME SE A SUA ARQUITETURA FOR ARM64 (ex: /usr/lib/jvm/java-17-openjdk-arm64)
# Ou se o comando 'ls' acima mostrar um caminho diferente
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-arm64
ENV SPARK_VERSION=3.4.3
ENV HADOOP_VERSION=3
# SPARK_HOME agora aponta diretamente para o diretório que será criado pelo tar
ENV SPARK_HOME=/opt/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}
# Adicionar Java e Spark ao PATH
ENV PATH=${JAVA_HOME}/bin:${SPARK_HOME}/bin:${PATH}
# Configurar PYTHONPATH para PySpark
ENV PYTHONPATH=${SPARK_HOME}/python:${SPARK_HOME}/python/lib/py4j-*.zip:${PYTHONPATH}

# Baixar e instalar Spark
# O tar vai descompactar para /opt/spark-3.4.3-bin-hadoop3 (que é o nosso SPARK_HOME)
RUN echo "Baixando Spark ${SPARK_VERSION}..." && \
    wget "https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz" -O "/tmp/spark.tgz" && \
    echo "Descompactando Spark em /opt/ ..." && \
    tar -xzf "/tmp/spark.tgz" -C /opt && \
    echo "Verificando se ${SPARK_HOME} existe..." && \
    test -d "${SPARK_HOME}" && \
    echo "Spark descompactado com sucesso em ${SPARK_HOME}" && \
    rm "/tmp/spark.tgz"

# Configurar permissões do Spark (opcional, mas pode ajudar)
RUN chmod -R 755 ${SPARK_HOME}

USER airflow

# Instalar PySpark, Delta e o provider do Airflow para Spark
RUN pip install --user --no-cache-dir \
    pyspark==${SPARK_VERSION} \
    delta-spark==2.4.0 \
    apache-airflow-providers-apache-spark

# Adicionar o diretório local de bin do usuário airflow ao PATH
ENV PATH="/home/airflow/.local/bin:${PATH}"
