# utils/interactive_tables.py - Professional Interactive DataFrames for Village Platform

import streamlit as st
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Any
import io
from datetime import datetime, date
import base64

def create_interactive_dataframe(
    df: pd.DataFrame,
    title: str = "Data Table",
    search_columns: Optional[List[str]] = None,
    filter_columns: Optional[List[str]] = None,
    export_formats: List[str] = ["CSV", "Excel"],
    max_height: int = 400,
    show_stats: bool = True,
    custom_formatting: Optional[Dict[str, str]] = None
) -> pd.DataFrame:
    """
    Create a professional interactive DataFrame with Village styling
    
    Args:
        df: DataFrame to display
        title: Table title
        search_columns: Columns to include in search functionality
        filter_columns: Columns to add filter widgets for
        export_formats: Export options ["CSV", "Excel", "JSON"]
        max_height: Maximum table height in pixels
        show_stats: Whether to show summary statistics
        custom_formatting: Column formatting dict {column: format_string}
    
    Returns:
        Filtered DataFrame based on user interactions
    """
    
    if df.empty:
        st.warning(f"No data available for {title}")
        return df
    
    # Village-themed styling for the table container
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #faf8f3 0%, #f5f1e8 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #5a7c47;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    ">
        <h3 style="color: #2d5016; margin: 0 0 1rem 0; font-size: 1.4rem;">
            {title}
        </h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Create a copy for filtering
    filtered_df = df.copy()
    
    # Control panel
    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
    
    with col1:
        # Global search functionality
        if search_columns is None:
            search_columns = [col for col in df.columns if df[col].dtype in ['object', 'string']]
        
        if search_columns:
            search_term = st.text_input(
                "Search",
                placeholder=f"Search across {', '.join(search_columns[:3])}{'...' if len(search_columns) > 3 else ''}",
                key=f"search_{title.replace(' ', '_')}"
            )
            
            if search_term:
                # Create search mask across specified columns
                search_mask = pd.Series([False] * len(filtered_df))
                for col in search_columns:
                    if col in filtered_df.columns:
                        search_mask |= filtered_df[col].astype(str).str.contains(
                            search_term, case=False, na=False
                        )
                filtered_df = filtered_df[search_mask]
    
    with col2:
        # Show number of records
        total_records = len(df)
        filtered_records = len(filtered_df)
        st.metric(
            "Records", 
            f"{filtered_records:,}",
            delta=f"{filtered_records - total_records:,}" if filtered_records != total_records else None
        )
    
    with col3:
        # Column selector
        available_columns = list(df.columns)
        selected_columns = st.multiselect(
            "Columns",
            available_columns,
            default=available_columns[:10],  # Show first 10 by default
            key=f"cols_{title.replace(' ', '_')}"
        )
        
        if not selected_columns:
            selected_columns = available_columns[:5]  # Fallback
    
    with col4:
        # Export functionality
        if export_formats:
            export_data = _create_export_options(filtered_df[selected_columns], title, export_formats)
            for format_name, (data, filename, mime_type) in export_data.items():
                st.download_button(
                    f"Download {format_name}",
                    data=data,
                    file_name=filename,
                    mime=mime_type,
                    key=f"export_{format_name}_{title.replace(' ', '_')}"
                )
    
    # Advanced filters
    if filter_columns:
        with st.expander("Advanced Filters", expanded=False):
            filter_cols = st.columns(min(len(filter_columns), 4))
            
            for i, col in enumerate(filter_columns):
                if col not in filtered_df.columns:
                    continue
                    
                with filter_cols[i % 4]:
                    if filtered_df[col].dtype in ['int64', 'float64']:
                        # Numeric filter
                        min_val = float(filtered_df[col].min())
                        max_val = float(filtered_df[col].max())
                        
                        if min_val != max_val:  # Only show slider if there's a range
                            selected_range = st.slider(
                                f"{col}",
                                min_value=min_val,
                                max_value=max_val,
                                value=(min_val, max_val),
                                key=f"filter_{col}_{title.replace(' ', '_')}"
                            )
                            filtered_df = filtered_df[
                                (filtered_df[col] >= selected_range[0]) & 
                                (filtered_df[col] <= selected_range[1])
                            ]
                    
                    elif filtered_df[col].dtype == 'object':
                        # Categorical filter
                        unique_values = sorted(filtered_df[col].unique().tolist())
                        if len(unique_values) <= 20:  # Only show multiselect for reasonable number of options
                            selected_values = st.multiselect(
                                f"{col}",
                                unique_values,
                                default=unique_values,
                                key=f"filter_{col}_{title.replace(' ', '_')}"
                            )
                            if selected_values:
                                filtered_df = filtered_df[filtered_df[col].isin(selected_values)]
                    
                    elif filtered_df[col].dtype in ['datetime64[ns]', 'datetime64[ns, UTC]']:
                        # Date filter
                        min_date = filtered_df[col].min().date() if not pd.isna(filtered_df[col].min()) else date.today()
                        max_date = filtered_df[col].max().date() if not pd.isna(filtered_df[col].max()) else date.today()
                        
                        if min_date != max_date:
                            selected_date_range = st.date_input(
                                f"{col}",
                                value=[min_date, max_date],
                                min_value=min_date,
                                max_value=max_date,
                                key=f"filter_{col}_{title.replace(' ', '_')}"
                            )
                            
                            if len(selected_date_range) == 2:
                                start_date, end_date = selected_date_range
                                filtered_df = filtered_df[
                                    (filtered_df[col].dt.date >= start_date) & 
                                    (filtered_df[col].dt.date <= end_date)
                                ]
    
    # Apply custom formatting
    display_df = filtered_df[selected_columns].copy()
    if custom_formatting:
        for col, format_str in custom_formatting.items():
            if col in display_df.columns:
                if format_str == 'currency':
                    display_df[col] = display_df[col].apply(lambda x: f"${x:,.2f}" if pd.notna(x) else "")
                elif format_str == 'percentage':
                    display_df[col] = display_df[col].apply(lambda x: f"{x:.2%}" if pd.notna(x) else "")
                elif format_str == 'datetime':
                    display_df[col] = pd.to_datetime(display_df[col]).dt.strftime('%Y-%m-%d %H:%M')
                elif isinstance(format_str, str) and '{' in format_str:
                    display_df[col] = display_df[col].apply(lambda x: format_str.format(x) if pd.notna(x) else "")
    
    # Display the interactive dataframe
    st.dataframe(
        display_df,
        use_container_width=True,
        height=max_height,
        hide_index=True,
        column_config=_get_column_config(display_df)
    )
    
    # Summary statistics
    if show_stats and not filtered_df.empty:
        with st.expander("Summary Statistics", expanded=False):
            numeric_cols = filtered_df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                stats_df = filtered_df[numeric_cols].describe().round(3)
                st.dataframe(stats_df, use_container_width=True)
            else:
                st.info("No numeric columns available for statistics")
    
    return filtered_df

def _create_export_options(df: pd.DataFrame, title: str, formats: List[str]) -> Dict[str, tuple]:
    """Create export data for different formats"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_data = {}
    
    if "CSV" in formats:
        csv_data = df.to_csv(index=False)
        export_data["CSV"] = (csv_data, f"{title}_{timestamp}.csv", "text/csv")
    
    if "Excel" in formats:
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=title[:30], index=False)  # Excel sheet name limit
        excel_data = excel_buffer.getvalue()
        export_data["Excel"] = (excel_data, f"{title}_{timestamp}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    
    if "JSON" in formats:
        json_data = df.to_json(orient='records', indent=2)
        export_data["JSON"] = (json_data, f"{title}_{timestamp}.json", "application/json")
    
    return export_data

def _get_column_config(df: pd.DataFrame) -> Dict[str, Any]:
    """Generate appropriate column configuration for streamlit dataframe"""
    config = {}
    
    for col in df.columns:
        if df[col].dtype in ['int64', 'float64']:
            config[col] = st.column_config.NumberColumn(
                col,
                help=f"Numeric values for {col}",
                format="%.3f" if df[col].dtype == 'float64' else "%d"
            )
        elif df[col].dtype == 'object' and col.lower() in ['url', 'link', 'website']:
            config[col] = st.column_config.LinkColumn(col)
        elif df[col].dtype in ['datetime64[ns]', 'datetime64[ns, UTC]']:
            config[col] = st.column_config.DatetimeColumn(
                col,
                help=f"Date and time for {col}",
                format="YYYY-MM-DD HH:mm:ss"
            )
        elif col.lower() in ['email']:
            config[col] = st.column_config.TextColumn(col, help="Email address")
        else:
            config[col] = st.column_config.TextColumn(col)
    
    return config

def create_summary_cards(df: pd.DataFrame, metric_configs: List[Dict[str, Any]]) -> None:
    """
    Create professional summary cards above tables
    
    Args:
        df: DataFrame for calculations
        metric_configs: List of dicts with keys: title, value_func, delta_func, help, format
    """
    if df.empty:
        return
    
    cols = st.columns(len(metric_configs))
    
    for i, config in enumerate(metric_configs):
        with cols[i]:
            try:
                value = config['value_func'](df)
                delta = config.get('delta_func', lambda x: None)(df) if 'delta_func' in config else None
                format_str = config.get('format', '{}')
                
                formatted_value = format_str.format(value) if value is not None else "N/A"
                
                st.metric(
                    label=config['title'],
                    value=formatted_value,
                    delta=delta,
                    help=config.get('help', '')
                )
            except Exception as e:
                st.metric(
                    label=config['title'],
                    value="Error",
                    help=f"Calculation error: {str(e)}"
                )

def create_professional_table_layout(
    df: pd.DataFrame,
    title: str,
    summary_metrics: Optional[List[Dict[str, Any]]] = None,
    **table_kwargs
) -> pd.DataFrame:
    """
    Create a complete professional table layout with metrics and interactive features
    """
    # Summary metrics at the top
    if summary_metrics:
        create_summary_cards(df, summary_metrics)
        st.markdown("---")
    
    # Interactive table
    return create_interactive_dataframe(df, title, **table_kwargs)

# Example usage and default configurations
TRAFFIC_INCIDENT_METRICS = [
    {
        'title': 'Total Incidents',
        'value_func': lambda df: len(df),
        'help': 'Total number of traffic incidents in the dataset'
    },
    {
        'title': 'Avg Severity',
        'value_func': lambda df: df['severity'].mean() if 'severity' in df.columns else None,
        'format': '{:.2f}',
        'help': 'Average severity level of incidents'
    },
    {
        'title': 'High Severity %',
        'value_func': lambda df: (df['severity'] > 2).mean() * 100 if 'severity' in df.columns else None,
        'format': '{:.1f}%',
        'help': 'Percentage of incidents with severity > 2'
    },
    {
        'title': 'Peak Hour',
        'value_func': lambda df: f"{df['hour'].mode().iloc[0]:02d}:00" if 'hour' in df.columns and not df.empty else None,
        'help': 'Most common hour for incidents'
    }
]

ANALYTICS_RESULTS_METRICS = [
    {
        'title': 'Sample Size',
        'value_func': lambda df: len(df),
        'format': '{:,}',
        'help': 'Number of records in analysis'
    },
    {
        'title': 'Date Range',
        'value_func': lambda df: f"{(df['timestamp'].max() - df['timestamp'].min()).days} days" if 'timestamp' in df.columns else None,
        'help': 'Time span of the data'
    },
    {
        'title': 'Locations',
        'value_func': lambda df: df['location'].nunique() if 'location' in df.columns else None,
        'help': 'Number of unique locations'
    },
    {
        'title': 'Data Quality',
        'value_func': lambda df: f"{(1 - df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100:.1f}%",
        'help': 'Percentage of non-missing values'
    }
]