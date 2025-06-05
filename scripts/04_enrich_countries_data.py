#!/usr/bin/env python3
"""
Script to enrich countries data with economic indicators.

This module joins the processed countries data with economic data (GDP per capita and HDI),
calculates additional metrics, and saves the enriched data in Delta format.
It includes proper error handling, logging, and type hints for better code maintainability.
"""

import logging
from typing import Dict, List, Optional, Any
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

class EnrichmentError(Exception):
    """Custom exception for data enrichment errors."""
    pass

def get_enriched_schema() -> StructType:
    """
    Define the schema for the enriched data.

    Returns:
        StructType: The schema definition for the enriched data
    """
    return StructType([
        StructField("country_code_3", StringType(), False),
        StructField("country_name", StringType(), True),
        StructField("region", StringType(), True),
        StructField("subregion", StringType(), True),
        StructField("population", IntegerType(), True),
        StructField("area", DoubleType(), True),
        StructField("population_density", DoubleType(), True),
        StructField("gdp_per_capita", DoubleType(), True),
        StructField("hdi", DoubleType(), True),
        StructField("development_status", StringType(), True)
    ])

def read_delta_table(spark: SparkSession, path: str, table_name: str) -> DataFrame:
    """
    Read a Delta table from the specified path.

    Args:
        spark: The SparkSession instance
        path: Path to the Delta table
        table_name: Name of the table for logging purposes

    Returns:
        DataFrame: The loaded Delta table

    Raises:
        EnrichmentError: If there are issues reading the table
    """
    try:
        logger.info(f"Reading {table_name} from: {path}")
        df = spark.read.format("delta").load(path)
        logger.info(f"Successfully read {table_name} with {df.count()} rows")
        return df
    except Exception as e:
        error_msg = f"Failed to read {table_name}: {str(e)}"
        logger.error(error_msg)
        raise EnrichmentError(error_msg) from e

def join_dataframes(df_countries: DataFrame, df_economic: DataFrame) -> DataFrame:
    """
    Join countries data with economic data.

    Args:
        df_countries: DataFrame containing countries data
        df_economic: DataFrame containing economic data

    Returns:
        DataFrame: The joined DataFrame

    Raises:
        EnrichmentError: If there are issues joining the dataframes
    """
    try:
        logger.info("Joining countries data with economic data...")
        
        # Join on country code
        df_joined = df_countries.join(
            df_economic,
            df_countries.country_code_3 == df_economic.country_code_3_econ,
            "left"
        )
        
        # Drop the redundant column
        df_joined = df_joined.drop("country_code_3_econ")
        
        logger.info(f"Joined data contains {df_joined.count()} rows")
        return df_joined
        
    except Exception as e:
        error_msg = f"Failed to join dataframes: {str(e)}"
        logger.error(error_msg)
        raise EnrichmentError(error_msg) from e

def calculate_development_status(df: DataFrame) -> DataFrame:
    """
    Calculate development status based on HDI and GDP per capita.

    Args:
        df: The input DataFrame

    Returns:
        DataFrame: DataFrame with added development status

    Raises:
        EnrichmentError: If there are issues calculating the status
    """
    try:
        logger.info("Calculating development status...")
        
        df = df.withColumn(
            "development_status",
            F.when(
                (F.col("hdi") >= 0.8) & (F.col("gdp_per_capita") >= 20000),
                "Developed"
            ).when(
                (F.col("hdi") >= 0.7) | (F.col("gdp_per_capita") >= 12000),
                "Emerging"
            ).otherwise("Developing")
        )
        
        # Log distribution of development status
        status_dist = df.groupBy("development_status").count().collect()
        for status in status_dist:
            logger.info(f"Development status '{status['development_status']}': {status['count']} countries")
            
        return df
        
    except Exception as e:
        error_msg = f"Failed to calculate development status: {str(e)}"
        logger.error(error_msg)
        raise EnrichmentError(error_msg) from e

def save_enriched_data(df: DataFrame, output_path: str) -> None:
    """
    Save the enriched data in Delta format.

    Args:
        df: The DataFrame to save
        output_path: Path where to save the Delta table

    Raises:
        EnrichmentError: If there are issues saving the data
    """
    try:
        logger.info(f"Saving enriched data to Delta: {output_path}")
        df.write.format("delta").mode("overwrite").save(output_path)
        logger.info("Enriched data successfully saved in Delta format")
    except Exception as e:
        error_msg = f"Failed to save Delta table: {str(e)}"
        logger.error(error_msg)
        raise EnrichmentError(error_msg) from e

def enrich_countries_data(
    spark: SparkSession,
    countries_path: str,
    economic_path: str,
    output_path: str
) -> None:
    """
    Enrich countries data with economic indicators.

    Args:
        spark: The SparkSession instance
        countries_path: Path to the countries Delta table
        economic_path: Path to the economic data Delta table
        output_path: Path where to save the enriched data

    Raises:
        EnrichmentError: If any step in the process fails
    """
    try:
        # Read input tables
        df_countries = read_delta_table(spark, countries_path, "countries data")
        df_economic = read_delta_table(spark, economic_path, "economic data")
        
        # Join dataframes
        df_joined = join_dataframes(df_countries, df_economic)
        
        # Calculate development status
        df_enriched = calculate_development_status(df_joined)
        
        # Save enriched data
        save_enriched_data(df_enriched, output_path)
        
    except Exception as e:
        error_msg = f"Data enrichment failed: {str(e)}"
        logger.error(error_msg)
        raise EnrichmentError(error_msg) from e

def main() -> None:
    """Main function to run the script."""
    parser = argparse.ArgumentParser(
        description="Enrich countries data with economic indicators.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--countries_path",
        required=True,
        help="Path to the countries Delta table"
    )
    parser.add_argument(
        "--economic_path",
        required=True,
        help="Path to the economic data Delta table"
    )
    parser.add_argument(
        "--output_path",
        required=True,
        help="Path to save the enriched Delta table"
    )
    
    args = parser.parse_args()
    
    try:
        spark = SparkSession.builder.appName("EnrichCountriesData").getOrCreate()
        enrich_countries_data(
            spark,
            args.countries_path,
            args.economic_path,
            args.output_path
        )
    except Exception as e:
        logger.error(f"Script failed: {str(e)}")
        raise
    finally:
        spark.stop()

if __name__ == "__main__":
    main()