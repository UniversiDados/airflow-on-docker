#!/usr/bin/env python3
"""
Script to process country data from JSON to Delta format.

This module processes country data from JSON format, applies schema validation,
flattens nested structures, calculates population density, and saves the result
in Delta format. It includes proper error handling, logging, and type hints
for better code maintainability.
"""

import logging
from typing import Dict, List, Optional, Any
import argparse
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType, ArrayType, LongType,
    DoubleType, MapType
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProcessingError(Exception):
    """Custom exception for data processing errors."""
    pass

def get_country_schema() -> StructType:
    """
    Define the schema for the country data.

    Returns:
        StructType: The schema definition for the country data
    """
    return StructType([
        StructField("name", StructType([
            StructField("common", StringType(), True),
            StructField("official", StringType(), True),
        ]), True),
        StructField("cca2", StringType(), True),
        StructField("cca3", StringType(), True),
        StructField("capital", ArrayType(StringType(), True), True),
        StructField("region", StringType(), True),
        StructField("subregion", StringType(), True),
        StructField("area", DoubleType(), True),
        StructField("population", LongType(), True),
        StructField("latlng", ArrayType(DoubleType(), True), True),
        StructField("currencies", MapType(StringType(), StructType([
            StructField("name", StringType(), True),
            StructField("symbol", StringType(), True)
        ])), True)
    ])

def read_json_data(spark: SparkSession, input_path: str) -> DataFrame:
    """
    Read and validate JSON data using the defined schema.

    Args:
        spark: The SparkSession instance
        input_path: Path to the input JSON file

    Returns:
        DataFrame: The validated DataFrame

    Raises:
        ProcessingError: If there are issues reading or validating the data
    """
    try:
        logger.info(f"Reading JSON data from: {input_path}")
        schema = get_country_schema()
        df = spark.read.json(input_path, schema=schema, multiLine=True)
        
        logger.info("Schema applied to raw DataFrame:")
        df.printSchema()
        
        return df
    except Exception as e:
        error_msg = f"Failed to read JSON data: {str(e)}"
        logger.error(error_msg)
        raise ProcessingError(error_msg) from e

def flatten_dataframe(df: DataFrame) -> DataFrame:
    """
    Flatten the nested DataFrame structure and extract relevant fields.

    Args:
        df: The input DataFrame with nested structure

    Returns:
        DataFrame: The flattened DataFrame
    """
    logger.info("Flattening DataFrame structure...")
    
    return df.select(
        F.col("name.common").alias("common_name"),
        F.col("name.official").alias("official_name"),
        F.col("cca2").alias("country_code_2"),
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
            F.col("latlng").isNotNull() & (F.size(F.col("latlng")) == 2),
            F.col("latlng").getItem(0)
        ).otherwise(None).alias("latitude"),
        F.when(
            F.col("latlng").isNotNull() & (F.size(F.col("latlng")) == 2),
            F.col("latlng").getItem(1)
        ).otherwise(None).alias("longitude"),
        F.when(
            F.col("currencies").isNotNull() & (F.size(F.map_keys(F.col("currencies"))) > 0),
            F.map_keys(F.col("currencies")).getItem(0)
        ).otherwise(None).alias("currency_code"),
        F.when(
            F.col("currencies").isNotNull() & (F.size(F.map_values(F.col("currencies"))) > 0),
            F.map_values(F.col("currencies")).getItem(0).getField("name")
        ).otherwise(None).alias("currency_name")
    )

def calculate_population_density(df: DataFrame) -> DataFrame:
    """
    Calculate population density for each country.

    Args:
        df: The input DataFrame with population and area columns

    Returns:
        DataFrame: DataFrame with added population_density column
    """
    logger.info("Calculating population density...")
    
    return df.withColumn(
        "population_density",
        F.when(
            F.col("area").isNotNull() & (F.col("area") > 0),
            F.col("population") / F.col("area")
        ).otherwise(None)
    )

def save_delta_table(df: DataFrame, output_path: str) -> None:
    """
    Save the processed DataFrame in Delta format.

    Args:
        df: The DataFrame to save
        output_path: Path where to save the Delta table

    Raises:
        ProcessingError: If there are issues saving the data
    """
    try:
        logger.info(f"Saving processed DataFrame to Delta: {output_path}")
        df.write.format("delta").mode("overwrite").save(output_path)
        logger.info("DataFrame successfully saved in Delta format")
    except Exception as e:
        error_msg = f"Failed to save Delta table: {str(e)}"
        logger.error(error_msg)
        raise ProcessingError(error_msg) from e

def process_data(spark: SparkSession, input_path: str, output_path_delta: str) -> None:
    """
    Process country data from JSON to Delta format.

    Args:
        spark: The SparkSession instance
        input_path: Path to the input JSON file
        output_path_delta: Path where to save the Delta table

    Raises:
        ProcessingError: If any step in the processing fails
    """
    try:
        # Read and validate data
        df = read_json_data(spark, input_path)
        
        # Process the data
        df_flat = flatten_dataframe(df)
        df_final = calculate_population_density(df_flat)
        
        # Save the result
        save_delta_table(df_final, output_path_delta)
        
    except Exception as e:
        error_msg = f"Data processing failed: {str(e)}"
        logger.error(error_msg)
        raise ProcessingError(error_msg) from e

def main() -> None:
    """Main function to run the script."""
    parser = argparse.ArgumentParser(
        description="Process country data from JSON to Delta format.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--input_path",
        required=True,
        help="Path to the input JSON file"
    )
    parser.add_argument(
        "--output_path_delta",
        required=True,
        help="Path to save the output Delta table"
    )
    
    args = parser.parse_args()
    
    try:
        spark = SparkSession.builder.appName("ProcessCountriesData").getOrCreate()
        process_data(spark, args.input_path, args.output_path_delta)
    except Exception as e:
        logger.error(f"Script failed: {str(e)}")
        raise
    finally:
        spark.stop()

if __name__ == "__main__":
    main()