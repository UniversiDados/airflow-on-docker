#!/usr/bin/env python3
"""
Script to create simulated economic data for countries.

This module generates simulated economic data (GDP per capita and HDI) for countries,
saving the results in Delta format. It includes proper error handling, logging,
and type hints for better code maintainability.
"""

import logging
from typing import Dict, List, Optional, Any
import argparse
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType
)
import random
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EconomicDataError(Exception):
    """Custom exception for economic data generation errors."""
    pass

def get_economic_schema() -> StructType:
    """
    Define the schema for the economic data.

    Returns:
        StructType: The schema definition for the economic data
    """
    return StructType([
        StructField("country_code_3_econ", StringType(), False),
        StructField("gdp_per_capita", DoubleType(), True),
        StructField("hdi", DoubleType(), True)
    ])

def read_country_codes(file_path: str) -> List[str]:
    """
    Read country codes from a text file.

    Args:
        file_path: Path to the file containing country codes

    Returns:
        List[str]: List of country codes

    Raises:
        EconomicDataError: If there are issues reading the file
    """
    try:
        logger.info(f"Reading country codes from: {file_path}")
        if not os.path.exists(file_path):
            raise EconomicDataError(f"Country codes file not found: {file_path}")
            
        with open(file_path, 'r') as f:
            # Read lines, strip whitespace, and filter out empty lines
            codes = [line.strip() for line in f if line.strip()]
            
        logger.info(f"Successfully read {len(codes)} country codes")
        return codes
        
    except Exception as e:
        error_msg = f"Failed to read country codes: {str(e)}"
        logger.error(error_msg)
        raise EconomicDataError(error_msg) from e

def generate_economic_data(spark: SparkSession, country_codes_path: str) -> DataFrame:
    """
    Generate simulated economic data for countries.

    Args:
        spark: The SparkSession instance
        country_codes_path: Path to the file containing country codes

    Returns:
        DataFrame: DataFrame containing simulated economic data

    Raises:
        EconomicDataError: If there are issues generating the data
    """
    try:
        logger.info("Generating simulated economic data...")
        
        # Read country codes from file
        country_codes = read_country_codes(country_codes_path)
        
        # Generate random economic data
        data = []
        for code in country_codes:
            # Generate realistic GDP per capita (in USD)
            gdp = random.uniform(1000, 100000)
            # Generate realistic HDI (between 0 and 1)
            hdi = random.uniform(0.4, 0.99)
            data.append((code, gdp, hdi))

        # Create DataFrame
        df = spark.createDataFrame(
            data,
            schema=get_economic_schema()
        )
        
        logger.info(f"Generated economic data for {df.count()} countries")
        return df
        
    except Exception as e:
        error_msg = f"Failed to generate economic data: {str(e)}"
        logger.error(error_msg)
        raise EconomicDataError(error_msg) from e

def save_delta_table(df: DataFrame, output_path: str) -> None:
    """
    Save the economic data DataFrame in Delta format.

    Args:
        df: The DataFrame to save
        output_path: Path where to save the Delta table

    Raises:
        EconomicDataError: If there are issues saving the data
    """
    try:
        logger.info(f"Saving economic data to Delta: {output_path}")
        df.write.format("delta").mode("overwrite").save(output_path)
        logger.info("Economic data successfully saved in Delta format")
    except Exception as e:
        error_msg = f"Failed to save Delta table: {str(e)}"
        logger.error(error_msg)
        raise EconomicDataError(error_msg) from e

def create_economic_data(
    spark: SparkSession,
    country_codes_path: str,
    output_path_delta: str
) -> None:
    """
    Create and save simulated economic data.

    Args:
        spark: The SparkSession instance
        country_codes_path: Path to the file containing country codes
        output_path_delta: Path where to save the Delta table

    Raises:
        EconomicDataError: If any step in the process fails
    """
    try:
        # Generate economic data
        df = generate_economic_data(spark, country_codes_path)
        
        # Save the data
        save_delta_table(df, output_path_delta)
        
    except Exception as e:
        error_msg = f"Economic data creation failed: {str(e)}"
        logger.error(error_msg)
        raise EconomicDataError(error_msg) from e

def main() -> None:
    """Main function to run the script."""
    parser = argparse.ArgumentParser(
        description="Create simulated economic data for countries.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--country_codes_path",
        required=True,
        help="Path to the file containing country codes"
    )
    parser.add_argument(
        "--output_path_delta",
        required=True,
        help="Path to save the output Delta table"
    )
    
    args = parser.parse_args()
    
    try:
        spark = SparkSession.builder.appName("CreateEconomicData").getOrCreate()
        create_economic_data(
            spark,
            args.country_codes_path,
            args.output_path_delta
        )
    except Exception as e:
        logger.error(f"Script failed: {str(e)}")
        raise
    finally:
        spark.stop()

if __name__ == "__main__":
    main()