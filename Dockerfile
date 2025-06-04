
FROM apache/airflow:2.8.1


USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
    default-jdk \ 
    wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


ENV JAVA_HOME=/usr/lib/jvm/default-java
ENV PATH=$JAVA_HOME/bin:$PATH


ENV SPARK_VERSION=3.3.0
ENV HADOOP_VERSION=3
ENV SPARK_HOME=/opt/spark
ENV PATH=$SPARK_HOME/bin:$PATH

RUN wget https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz -O /tmp/spark.tgz && \
    tar -xzf /tmp/spark.tgz -C /opt && \
    mv /opt/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION} ${SPARK_HOME} && \
    rm /tmp/spark.tgz


USER airflow

RUN pip install --user --no-cache-dir \
    apache-airflow-providers-apache-spark \
    pyspark==${SPARK_VERSION}

ENV PATH="/home/airflow/.local/bin:${PATH}"