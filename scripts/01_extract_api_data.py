#!/usr/bin/env python3
"""
Script to extract country data from the REST Countries API.

This module handles the extraction of country data from the REST Countries API,
saving the results in JSON format. It includes proper error handling, logging,
and type hints for better code maintainability.
"""

import json
import logging
import os
from typing import Dict, List, Optional, Any
import requests
import argparse
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
API_BASE_URL = "https://restcountries.com/v3.1"
API_ENDPOINT = "all"
REQUIRED_FIELDS = [
    "name",      # Country name
    "cca2",      # 2-letter country code
    "cca3",      # 3-letter country code
    "capital",   # Capital city
    "region",    # Region
    "subregion", # Subregion
    "area",      # Area in square kilometers
    "population",# Population
    "latlng",    # Latitude and longitude
    "currencies" # Currency information
]

class APIError(Exception):
    """Custom exception for API-related errors."""
    pass

def build_api_url(base_url: str, endpoint: str, fields: List[str]) -> str:
    """
    Build the complete API URL with fields parameter.

    Args:
        base_url: The base URL of the API
        endpoint: The API endpoint to call
        fields: List of fields to request from the API

    Returns:
        str: The complete API URL with fields parameter
    """
    url = urljoin(base_url, endpoint)
    fields_param = ','.join(fields)
    return f"{url}?fields={fields_param}"

def make_api_request(url: str) -> List[Dict[str, Any]]:
    """
    Make a request to the REST Countries API.

    Args:
        url: The complete API URL to call

    Returns:
        List[Dict[str, Any]]: The JSON response from the API

    Raises:
        APIError: If the API request fails
        requests.RequestException: For network-related errors
    """
    try:
        logger.info(f"Making request to API: {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"Successfully retrieved data for {len(data)} countries")
        return data
    except requests.exceptions.RequestException as e:
        error_msg = f"API request failed: {str(e)}"
        if hasattr(e, 'response') and e.response is not None:
            error_msg += f"\nStatus code: {e.response.status_code}"
            error_msg += f"\nResponse content: {e.response.text}"
        logger.error(error_msg)
        raise APIError(error_msg) from e

def save_json_data(data: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save the API response data to a JSON file.

    Args:
        data: The data to save
        output_path: Path where to save the JSON file

    Raises:
        OSError: If there are issues creating directories or writing the file
    """
    try:
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logger.info(f"Data successfully saved to: {output_path}")
    except OSError as e:
        error_msg = f"Failed to save data to {output_path}: {str(e)}"
        logger.error(error_msg)
        raise

def extract_data(api_url: str, output_path: str) -> None:
    """
    Extract country data from the API and save it to a JSON file.

    Args:
        api_url: The base URL for the API
        output_path: Path where to save the JSON file

    Raises:
        APIError: If the API request fails
        OSError: If there are issues saving the file
    """
    try:
        # Build the complete API URL with fields
        complete_url = build_api_url(api_url, API_ENDPOINT, REQUIRED_FIELDS)
        
        # Get data from API
        countries_data = make_api_request(complete_url)
        
        # Save the data
        save_json_data(countries_data, output_path)
        
    except (APIError, OSError) as e:
        logger.error(f"Data extraction failed: {str(e)}")
        raise

def main() -> None:
    """Main function to run the script."""
    parser = argparse.ArgumentParser(
        description="Extract country data from the REST Countries API.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--output_path",
        required=True,
        help="Path to save the output JSON file"
    )
    
    args = parser.parse_args()
    
    try:
        extract_data(API_BASE_URL, args.output_path)
    except Exception as e:
        logger.error(f"Script failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()