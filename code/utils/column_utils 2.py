#!/usr/bin/env python3
# utils/column_utils.py

"""
This file is for column utilities for handling different column name formats across data sources
"""

import pandas as pd
from typing import Tuple, Optional


def get_coordinate_columns(df: pd.DataFrame) -> Tuple[Optional[str], Optional[str]]:
    """
    Get the correct coordinate column names from a DataFrame.
    
    Args:
        df: DataFrame to check for coordinate columns
        
    Returns:
        Tuple of (latitude_column, longitude_column) or (None, None) if not found
    """
    # Check for full names first
    if 'latitude' in df.columns and 'longitude' in df.columns:
        return 'latitude', 'longitude'
    
    # Check for abbreviated names
    if 'lat' in df.columns and 'lng' in df.columns:
        return 'lat', 'lng'
    
    # Check for alternative abbreviations
    if 'lat' in df.columns and 'lon' in df.columns:
        return 'lat', 'lon'
    
    return None, None


def standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize column names to a consistent format.
    
    Args:
        df: DataFrame to standardize
        
    Returns:
        DataFrame with standardized column names
    """
    df = df.copy()
    
    # Coordinate columns
    if 'latitude' in df.columns:
        df = df.rename(columns={'latitude': 'lat'})
    if 'longitude' in df.columns:
        df = df.rename(columns={'longitude': 'lng'})
    if 'lon' in df.columns:
        df = df.rename(columns={'lon': 'lng'})
    
    # Common alternative column names
    column_mappings = {
        'incident_id': 'id',
        'external_id': 'id',
        'incident_type': 'type',
        'Length_of_Time(Hours)': 'length_hours',
        'rush_hour': 'rush'
    }
    
    for old_name, new_name in column_mappings.items():
        if old_name in df.columns and new_name not in df.columns:
            df = df.rename(columns={old_name: new_name})
    
    return df


def check_required_columns(df: pd.DataFrame, required_columns: list) -> Tuple[bool, list]:
    """
    Check if DataFrame has all required columns.
    
    Args:
        df: DataFrame to check
        required_columns: List of required column names
        
    Returns:
        Tuple of (all_present, missing_columns)
    """
    missing_columns = [col for col in required_columns if col not in df.columns]
    return len(missing_columns) == 0, missing_columns


def get_flexible_column_reference(df: pd.DataFrame, column_aliases: dict) -> dict:
    """
    Get flexible column references based on what's available in the DataFrame.
    
    Args:
        df: DataFrame to check
        column_aliases: Dict mapping standard names to list of possible aliases
                       e.g., {'lat': ['latitude', 'lat'], 'lng': ['longitude', 'lng', 'lon']}
        
    Returns:
        Dict mapping standard names to actual column names found in DataFrame
    """
    column_map = {}
    
    for standard_name, aliases in column_aliases.items():
        for alias in aliases:
            if alias in df.columns:
                column_map[standard_name] = alias
                break
        
        # If no alias found, set to None
        if standard_name not in column_map:
            column_map[standard_name] = None
    
    return column_map


def safe_column_operation(df: pd.DataFrame, columns: list, operation: str = 'select') -> pd.DataFrame:
    """
    Safely perform operations on columns that may or may not exist.
    
    Args:
        df: DataFrame to operate on
        columns: List of column names to use
        operation: Type of operation ('select', 'drop', etc.)
        
    Returns:
        DataFrame with operation applied to existing columns only
    """
    existing_columns = [col for col in columns if col in df.columns]
    
    if not existing_columns:
        if operation == 'select':
            return pd.DataFrame()  # Return empty DataFrame
        else:
            return df  # Return original DataFrame
    
    if operation == 'select':
        return df[existing_columns]
    elif operation == 'drop':
        return df.drop(columns=existing_columns)
    else:
        return df


# Common column alias definitions
COORDINATE_ALIASES = {
    'lat': ['latitude', 'lat'],
    'lng': ['longitude', 'lng', 'lon']
}

TRAFFIC_INCIDENT_ALIASES = {
    'id': ['id', 'incident_id', 'external_id'],
    'lat': ['latitude', 'lat'],
    'lng': ['longitude', 'lng', 'lon'],
    'timestamp': ['timestamp', 'time', 'datetime'],
    'location': ['location', 'place', 'area'],
    'description': ['description', 'desc', 'details'],
    'severity': ['severity', 'level', 'priority'],
    'type': ['type', 'incident_type', 'category'],
    'length_hours': ['length_hours', 'Length_of_Time(Hours)', 'duration']
}