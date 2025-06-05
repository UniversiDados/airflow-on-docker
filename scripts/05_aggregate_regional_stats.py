#!/usr/bin/env python3
"""
Script to aggregate regional statistics from enriched countries data.

This module calculates various statistics (population, GDP, HDI) by region and subregion,
saving the aggregated data in Delta format. It includes proper error handling,
logging, and type hints for better code maintainability.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
import argparse
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, IntegerType
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AggregationError(Exception):
    """Custom exception for data aggregation errors."""
    pass

def get_regional_stats_schema() -> StructType:
    """
    Define the schema for the regional statistics.

    Returns:
        StructType: The schema definition for the regional statistics
    """
    return StructType([
        StructField("region", StringType(), False),
        StructField("subregion", StringType(), False),
        StructField("total_population", IntegerType(), True),
        StructField("avg_population_density", DoubleType(), True),
        StructField("avg_gdp_per_capita", DoubleType(), True),
        StructField("avg_hdi", DoubleType(), True),
        StructField("developed_countries", IntegerType(), True),
        StructField("emerging_countries", IntegerType(), True),
        StructField("developing_countries", IntegerType(), True),
        StructField("total_countries", IntegerType(), True)
    ])

def read_enriched_data(spark: SparkSession, input_path: str) -> DataFrame:
    """
    Read the enriched countries data.

    Args:
        spark: The SparkSession instance
        input_path: Path to the enriched data Delta table

    Returns:
        DataFrame: The loaded enriched data

    Raises:
        AggregationError: If there are issues reading the data
    """
    try:
        logger.info(f"Reading enriched data from: {input_path}")
        df = spark.read.format("delta").load(input_path)
        logger.info(f"Successfully read enriched data with {df.count()} rows")
        return df
    except Exception as e:
        error_msg = f"Failed to read enriched data: {str(e)}"
        logger.error(error_msg)
        raise AggregationError(error_msg) from e

def calculate_regional_stats(df: DataFrame) -> DataFrame:
    """
    Calculate statistics for each region and subregion.

    Args:
        df: The enriched countries DataFrame

    Returns:
        DataFrame: DataFrame containing regional statistics

    Raises:
        AggregationError: If there are issues calculating the statistics
    """
    try:
        logger.info("Calculating regional statistics...")
        
        # Calculate statistics by region and subregion
        df_stats = df.groupBy("region", "subregion").agg(
            F.sum("population").alias("total_population"),
            F.avg("population_density").alias("avg_population_density"),
            F.avg("gdp_per_capita").alias("avg_gdp_per_capita"),
            F.avg("hdi").alias("avg_hdi"),
            F.sum(F.when(F.col("development_status") == "Developed", 1).otherwise(0)).alias("developed_countries"),
            F.sum(F.when(F.col("development_status") == "Emerging", 1).otherwise(0)).alias("emerging_countries"),
            F.sum(F.when(F.col("development_status") == "Developing", 1).otherwise(0)).alias("developing_countries"),
            F.count("*").alias("total_countries")
        )
        
        # Round numeric columns
        df_stats = df_stats.withColumn(
            "avg_population_density",
            F.round(F.col("avg_population_density"), 2)
        ).withColumn(
            "avg_gdp_per_capita",
            F.round(F.col("avg_gdp_per_capita"), 2)
        ).withColumn(
            "avg_hdi",
            F.round(F.col("avg_hdi"), 3)
        )
        
        # Log some statistics
        logger.info("Regional statistics calculated:")
        for row in df_stats.select("region", "total_countries", "total_population").collect():
            logger.info(
                f"Region '{row['region']}': {row['total_countries']} countries, "
                f"total population: {row['total_population']:,}"
            )
            
        return df_stats
        
    except Exception as e:
        error_msg = f"Failed to calculate regional statistics: {str(e)}"
        logger.error(error_msg)
        raise AggregationError(error_msg) from e

def save_regional_stats(df: DataFrame, output_path: str) -> None:
    """
    Save the regional statistics in Delta format.

    Args:
        df: The DataFrame to save
        output_path: Path where to save the Delta table

    Raises:
        AggregationError: If there are issues saving the data
    """
    try:
        logger.info(f"Saving regional statistics to Delta: {output_path}")
        df.write.format("delta").mode("overwrite").save(output_path)
        logger.info("Regional statistics successfully saved in Delta format")
    except Exception as e:
        error_msg = f"Failed to save Delta table: {str(e)}"
        logger.error(error_msg)
        raise AggregationError(error_msg) from e

def aggregate_regional_stats(
    spark: SparkSession,
    input_path: str,
    output_path: str
) -> None:
    """
    Aggregate regional statistics from enriched countries data.

    Args:
        spark: The SparkSession instance
        input_path: Path to the enriched data Delta table
        output_path: Path where to save the regional statistics

    Raises:
        AggregationError: If any step in the process fails
    """
    try:
        # Read enriched data
        df = read_enriched_data(spark, input_path)
        
        # Calculate regional statistics
        df_stats = calculate_regional_stats(df)
        
        # Save regional statistics
        save_regional_stats(df_stats, output_path)
        
    except Exception as e:
        error_msg = f"Regional statistics aggregation failed: {str(e)}"
        logger.error(error_msg)
        raise AggregationError(error_msg) from e

def main() -> None:
    """Main function to run the script."""
    parser = argparse.ArgumentParser(
        description="Aggregate regional statistics from enriched countries data.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--input_path",
        required=True,
        help="Path to the enriched data Delta table"
    )
    parser.add_argument(
        "--output_path",
        required=True,
        help="Path to save the regional statistics Delta table"
    )
    
    args = parser.parse_args()
    
    try:
        spark = SparkSession.builder.appName("AggregateRegionalStats").getOrCreate()
        aggregate_regional_stats(
            spark,
            args.input_path,
            args.output_path
        )
    except Exception as e:
        logger.error(f"Script failed: {str(e)}")
        raise
    finally:
        spark.stop()

if __name__ == "__main__":
    main()