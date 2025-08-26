# pages/analytics.py - Statistical Analysis and Data Modeling Module

import streamlit as st
import pandas as pd
import numpy as np
import datetime
import os
import seaborn as sns
import matplotlib.pyplot as plt
from scipy import stats
from scipy.stats import sem, t
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.neighbors import KNeighborsRegressor, KNeighborsClassifier
from sklearn.svm import SVR, SVC
from sklearn.metrics import mean_squared_error, r2_score, classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler, LabelEncoder
import warnings
warnings.filterwarnings('ignore')

# Import theme manager
try:
    from utils.theme_manager import apply_village_theme, create_village_header, get_village_colors
except ImportError:
    st.error("Theme manager not available")

# Import interactive tables utility
try:
    from utils.interactive_tables import (
        create_interactive_dataframe,
        create_professional_table_layout,
        TRAFFIC_INCIDENT_METRICS,
        ANALYTICS_RESULTS_METRICS
    )
    INTERACTIVE_TABLES_AVAILABLE = True
except ImportError:
    INTERACTIVE_TABLES_AVAILABLE = False
    st.warning("Interactive tables utility not available. Using basic dataframes.")

# Get Village colors from theme manager
VILLAGE_COLORS = get_village_colors()

# Configure Seaborn with Village theme
sns.set_theme(style="whitegrid", palette=VILLAGE_COLORS['palette'])
plt.rcParams.update({
    'figure.facecolor': VILLAGE_COLORS['neutral'],
    'axes.facecolor': 'white',
    'grid.color': '#e0e0e0',
    'text.color': VILLAGE_COLORS['primary'],
    'axes.labelcolor': VILLAGE_COLORS['primary'],
    'xtick.color': VILLAGE_COLORS['primary'],
    'ytick.color': VILLAGE_COLORS['primary']
})

def show():
    # Apply Village theme
    apply_village_theme()
    
    # Display the Analytics page with standardized header
    create_village_header(
        "Traffic Analytics & Data Modeling",
        "Advanced statistical analysis and predictive modeling for traffic planning"
    )
    
    # Load data using improved data sync
    try:
        # Import data sync utility
        from utils.data_sync import get_traffic_data
        
        # Get data from the past 30 days for analysis
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=30)
        
        df = get_traffic_data(
            start_date=start_date,
            end_date=end_date
        )
        
        if df.empty:
            st.warning("No data available for analysis")
            st.info("💡 The system is collecting real-time data. Please wait for data to accumulate.")
            return
        
        st.success(f"Loaded {len(df)} records from the last 30 days")
        st.write(f"Columns available: {list(df.columns)}")
        
        # Ensure required columns exist
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        if 'date' not in df.columns:
            df['date'] = df['timestamp'].dt.date
        if 'hour' not in df.columns:
            df['hour'] = df['timestamp'].dt.hour
        if 'day_of_week' not in df.columns:
            df['day_of_week'] = df['timestamp'].dt.day_name()
        
        # Handle column name variations
        if 'lat' in df.columns and 'latitude' not in df.columns:
            df['latitude'] = df['lat']
        if 'lng' in df.columns and 'longitude' not in df.columns:
            df['longitude'] = df['lng']
            
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.write("Current working directory:", os.getcwd())
        return
    
    # Sidebar for analysis options
    st.sidebar.header("Analysis Configuration")
    
    analysis_type = st.sidebar.selectbox(
        "Analysis Type:",
        ["Descriptive Statistics", "Trend Analysis", "Statistical Tests", 
         "Predictive Modeling", "Bias Detection"]
    )
    
    # Date range filter
    st.sidebar.subheader("Date Range")
    min_date = df['date'].min()
    max_date = df['date'].max()
    
    date_range = st.sidebar.date_input(
        "Select Date Range:",
        value=[min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )
    
    if len(date_range) == 2:
        filtered_df = df[(df['date'] >= date_range[0]) & (df['date'] <= date_range[1])]
    else:
        filtered_df = df
    
    # Location filter
    try:
        locations = ['All'] + sorted(df['location'].unique().tolist())
        selected_location = st.sidebar.selectbox("🏘️ Location:", locations)
    except KeyError as e:
        st.error(f"Column not found: {e}")
        st.write("Available columns:", df.columns.tolist())
        return
    
    if selected_location != 'All':
        filtered_df = filtered_df[filtered_df['location'] == selected_location]
    
    # Display current dataset info
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Dataset Info")
    st.sidebar.info(f"""
    **Records:** {len(filtered_df):,}
    **Date Range:** {filtered_df['date'].min()} to {filtered_df['date'].max()}
    **Locations:** {filtered_df['location'].nunique()}
    **Incident Types:** {filtered_df['type'].nunique()}
    """)
    
    # Main content based on selected analysis
    if analysis_type == "Descriptive Statistics":
        show_descriptive_stats(filtered_df)
    elif analysis_type == "Trend Analysis":
        show_trend_analysis(filtered_df)
    elif analysis_type == "Statistical Tests":
        show_statistical_tests(filtered_df)
    elif analysis_type == "Predictive Modeling":
        show_predictive_modeling(filtered_df)
    elif analysis_type == "Bias Detection":
        show_bias_detection(filtered_df)

def show_descriptive_stats(df):
    """Display descriptive statistics and distributions"""
    
    st.subheader("Descriptive Statistics")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Incidents", len(df))
    with col2:
        st.metric("Avg Severity", f"{df['severity'].mean():.2f}")
    with col3:
        st.metric("Avg Duration", f"{df['Length_of_Time(Hours)'].mean():.1f}h")
    with col4:
        st.metric("Peak Hour", f"{df['hour'].mode().iloc[0]}:00")
    
    # Confidence Intervals Section
    st.subheader("Statistical Confidence Intervals (95%)")
    
    def calculate_ci(data, confidence=0.95):
        """Calculate confidence interval for a given dataset"""
        data_clean = data.dropna()
        if len(data_clean) == 0:
            return np.nan, np.nan
        n = len(data_clean)
        mean = np.mean(data_clean)
        se = sem(data_clean)
        h = se * t.ppf((1 + confidence) / 2., n-1)
        return mean - h, mean + h
    
    # Calculate confidence intervals for key metrics
    severity_ci = calculate_ci(df['severity'])
    duration_ci = calculate_ci(df['Length_of_Time(Hours)'])
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Severity Mean", f"{df['severity'].mean():.3f}")
        st.caption(f"95% CI: [{severity_ci[0]:.3f}, {severity_ci[1]:.3f}]")
    with col2:
        st.metric("Duration Mean", f"{df['Length_of_Time(Hours)'].mean():.2f}h")
        st.caption(f"95% CI: [{duration_ci[0]:.2f}h, {duration_ci[1]:.2f}h]")
    with col3:
        # Sample size for statistical power
        st.metric("Sample Size", f"{len(df):,}")
        st.caption("For statistical power analysis")
    with col4:
        # Standard errors
        severity_se = sem(df['severity'].dropna())
        st.metric("Severity SE", f"{severity_se:.4f}")
        st.caption("Standard Error of Mean")
    
    # Statistical summary with interactive table
    st.subheader("Statistical Summary")
    
    numeric_cols = ["severity", "Length_of_Time(Hours)", "incidents_per_town_hour", "incidents_per_type"]
    summary_stats = df[numeric_cols].describe().round(3)
    
    if INTERACTIVE_TABLES_AVAILABLE:
        # Convert describe() output to a more readable format
        summary_df = summary_stats.T.reset_index()
        summary_df.rename(columns={'index': 'Metric'}, inplace=True)
        
        create_interactive_dataframe(
            summary_df,
            title="Statistical Summary",
            search_columns=['Metric'],
            export_formats=["CSV", "Excel"],
            max_height=300,
            show_stats=False
        )
    else:
        st.dataframe(summary_stats, use_container_width=True)
    
    # Distribution plots with Seaborn
    st.subheader("Distribution Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Severity distribution
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.histplot(data=df, x="severity", ax=ax, color=VILLAGE_COLORS['primary'], alpha=0.7)
        ax.set_title("Incident Severity Distribution", fontsize=14, fontweight='bold', color=VILLAGE_COLORS['primary'])
        ax.set_xlabel("Severity Level", color=VILLAGE_COLORS['primary'])
        ax.set_ylabel("Frequency", color=VILLAGE_COLORS['primary'])
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()
    
    with col2:
        # Duration distribution
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.boxplot(data=df, y='Length_of_Time(Hours)', ax=ax, color=VILLAGE_COLORS['secondary'])
        ax.set_title("Incident Duration Distribution", fontsize=14, fontweight='bold', color=VILLAGE_COLORS['primary'])
        ax.set_ylabel("Duration (Hours)", color=VILLAGE_COLORS['primary'])
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()
    
    # Correlation matrix with Seaborn
    st.subheader("Correlation Analysis")
    
    correlation_matrix = df[numeric_cols].corr()
    
    fig, ax = plt.subplots(figsize=(10, 8))
    mask = np.triu(np.ones_like(correlation_matrix, dtype=bool))
    sns.heatmap(
        correlation_matrix, 
        annot=True, 
        cmap='RdBu_r', 
        vmin=-1, 
        vmax=1, 
        center=0,
        square=True, 
        mask=mask,
        cbar_kws={"shrink": .8},
        ax=ax
    )
    ax.set_title("Correlation Matrix", fontsize=16, fontweight='bold', color=VILLAGE_COLORS['primary'])
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

def show_trend_analysis(df):
    """Display temporal trend analysis"""
    
    st.subheader("Trend Analysis")
    
    # Time series analysis
    st.subheader("Temporal Patterns")
    
    # Daily incidents trend with Seaborn
    daily_incidents = df.groupby('date').size().reset_index(name='incident_count')
    daily_incidents['date'] = pd.to_datetime(daily_incidents['date'])
    
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.lineplot(data=daily_incidents, x='date', y='incident_count', ax=ax, 
                color=VILLAGE_COLORS['primary'], linewidth=2.5, marker='o', markersize=4)
    ax.set_title("Daily Incident Count Trend", fontsize=16, fontweight='bold', color=VILLAGE_COLORS['primary'])
    ax.set_xlabel("Date", color=VILLAGE_COLORS['primary'])
    ax.set_ylabel("Incident Count", color=VILLAGE_COLORS['primary'])
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()
    
    # Interactive table for daily trends
    if INTERACTIVE_TABLES_AVAILABLE:
        daily_incidents['date'] = daily_incidents['date'].dt.strftime('%Y-%m-%d')
        create_interactive_dataframe(
            daily_incidents,
            title="Daily Incident Trends",
            search_columns=['date'],
            filter_columns=['incident_count'],
            export_formats=["CSV", "Excel"],
            max_height=300
        )
    
    # Hourly patterns
    col1, col2 = st.columns(2)
    
    with col1:
        hourly_incidents = df.groupby('hour').size().reset_index(name='incident_count')
        
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(data=hourly_incidents, x='hour', y='incident_count', ax=ax, 
                   color=VILLAGE_COLORS['secondary'], alpha=0.8)
        ax.set_title("Incidents by Hour of Day", fontsize=14, fontweight='bold', color=VILLAGE_COLORS['primary'])
        ax.set_xlabel("Hour of Day", color=VILLAGE_COLORS['primary'])
        ax.set_ylabel("Incident Count", color=VILLAGE_COLORS['primary'])
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()
    
    with col2:
        dow_incidents = df.groupby('day_of_week').size().reset_index(name='incident_count')
        # Reorder days
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        dow_incidents['day_of_week'] = pd.Categorical(dow_incidents['day_of_week'], categories=day_order, ordered=True)
        dow_incidents = dow_incidents.sort_values('day_of_week')
        
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(data=dow_incidents, x='day_of_week', y='incident_count', ax=ax, 
                   color=VILLAGE_COLORS['accent'], alpha=0.8)
        ax.set_title("Incidents by Day of Week", fontsize=14, fontweight='bold', color=VILLAGE_COLORS['primary'])
        ax.set_xlabel("Day of Week", color=VILLAGE_COLORS['primary'])
        ax.set_ylabel("Incident Count", color=VILLAGE_COLORS['primary'])
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()
    
    # Location-based analysis
    st.subheader("Location Analysis")
    
    location_stats = df.groupby('location').agg({
        'severity': 'mean',
        'Length_of_Time(Hours)': 'mean',
        'location': 'count'
    }).rename(columns={'location': 'incident_count'}).reset_index()
    
    # Top locations by incident count
    top_locations = location_stats.nlargest(10, 'incident_count')
    
    fig_locations = px.bar(
        top_locations,
        x='location',
        y='incident_count',
        title="Top 10 Locations by Incident Count",
        color='severity',
        color_continuous_scale='Reds'
    )
    fig_locations.update_layout(height=500)
    fig_locations.update_xaxes(tickangle=45)
    st.plotly_chart(fig_locations, use_container_width=True)

def show_statistical_tests(df):
    """Display statistical hypothesis tests"""
    
    st.subheader("Hypothesis Testing")
    
    # ANOVA Test
    st.subheader("ANOVA: Incident Duration by Location")
    
    # Filter locations with sufficient data
    location_counts = df['location'].value_counts()
    valid_locations = location_counts[location_counts >= 5].index
    
    if len(valid_locations) >= 2:
        anova_df = df[df['location'].isin(valid_locations)]
        
        # Prepare data for ANOVA
        groups = [anova_df[anova_df['location'] == loc]['Length_of_Time(Hours)'].dropna() 
                 for loc in valid_locations]
        
        # Perform ANOVA
        f_stat, p_value = stats.f_oneway(*groups)
        
        # Calculate effect size (eta-squared)
        def calculate_eta_squared(f_stat, group_sizes):
            """Calculate eta-squared effect size for ANOVA"""
            total_n = sum(group_sizes)
            k = len(group_sizes)  # number of groups
            eta_squared = (f_stat * (k - 1)) / (f_stat * (k - 1) + (total_n - k))
            return eta_squared
        
        group_sizes = [len(group) for group in groups]
        eta_squared = calculate_eta_squared(f_stat, group_sizes)
        
        # Effect size interpretation
        if eta_squared < 0.01:
            effect_interpretation = "Small"
        elif eta_squared < 0.06:
            effect_interpretation = "Medium"
        else:
            effect_interpretation = "Large"
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("F-Statistic", f"{f_stat:.4f}")
        with col2:
            st.metric("P-Value", f"{p_value:.6f}")
        with col3:
            significance = "Significant" if p_value < 0.05 else "Not Significant"
            st.metric("Result", significance)
        with col4:
            st.metric("Effect Size (η²)", f"{eta_squared:.4f}")
            st.caption(f"({effect_interpretation} effect)")
        
        # Interpretation
        if p_value < 0.05:
            st.success("**Significant difference** in incident duration between locations (p < 0.05)")
        else:
            st.info("**No significant difference** in incident duration between locations (p ≥ 0.05)")
        
        # Box plot for visual comparison
        fig_anova = px.box(
            anova_df,
            x='location',
            y='Length_of_Time(Hours)',
            title="Incident Duration by Location (ANOVA Analysis)",
            color_discrete_sequence=['#2d5016']
        )
        fig_anova.update_xaxes(tickangle=45)
        st.plotly_chart(fig_anova, use_container_width=True)
    else:
        st.warning("Insufficient data for ANOVA analysis. Need at least 5 incidents per location.")
    
    # T-test: Rush hour vs Non-rush hour
    st.subheader("T-Test: Rush Hour vs Non-Rush Hour Severity")
    
    if 'rush' in df.columns:
        rush_severity = df[df['rush'] == 1]['severity'].dropna()
        non_rush_severity = df[df['rush'] == 0]['severity'].dropna()
        
        if len(rush_severity) > 0 and len(non_rush_severity) > 0:
            t_stat, t_p_value = stats.ttest_ind(rush_severity, non_rush_severity)
            
            # Basic descriptive statistics for both groups
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Rush Hour Mean", f"{rush_severity.mean():.3f}")
            with col2:
                st.metric("Non-Rush Mean", f"{non_rush_severity.mean():.3f}")
            with col3:
                st.metric("T-Statistic", f"{t_stat:.4f}")
            with col4:
                st.metric("P-Value", f"{t_p_value:.6f}")
            
            if t_p_value < 0.05:
                st.success("**Significant difference** in severity between rush and non-rush hours")
            else:
                st.info("**No significant difference** in severity between rush and non-rush hours")
    
    # Normality Testing - Essential for validating t-test and ANOVA assumptions
    st.subheader("Normality Testing")
    st.markdown("**Important**: Many statistical tests assume data follows a normal distribution")
    
    from scipy.stats import shapiro, normaltest
    
    # Test normality of key variables
    variables_to_test = ['severity', 'Length_of_Time(Hours)']
    
    normality_results = []
    for var in variables_to_test:
        if var in df.columns:
            data = df[var].dropna()
            if len(data) > 3:  # Minimum for Shapiro-Wilk
                # Use sample if dataset is large (Shapiro-Wilk works best with smaller samples)
                sample_data = data.sample(min(5000, len(data)), random_state=42)
                shapiro_stat, shapiro_p = shapiro(sample_data)
                
                # Interpretation
                is_normal = "Yes" if shapiro_p > 0.05 else "No"
                
                normality_results.append({
                    'Variable': var.replace('_', ' ').title(),
                    'Sample Size': len(sample_data),
                    'Shapiro-Wilk Statistic': f"{shapiro_stat:.4f}",
                    'P-Value': f"{shapiro_p:.6f}",
                    'Normal Distribution?': is_normal
                })
    
    if normality_results:
        normality_df = pd.DataFrame(normality_results)
        st.dataframe(normality_df, use_container_width=True)
        
        st.info("**Interpretation**: p > 0.05 suggests data follows normal distribution. If p ≤ 0.05, consider using non-parametric tests.")
    
    # Chi-square test: Incident type vs Day of week
    st.subheader("Chi-Square: Incident Type vs Day of Week")
    
    if len(df['type'].unique()) > 1 and len(df['day_of_week'].unique()) > 1:
        contingency_table = pd.crosstab(df['type'], df['day_of_week'])
        chi2, chi2_p, dof, expected = stats.chi2_contingency(contingency_table)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Chi-Square", f"{chi2:.4f}")
        with col2:
            st.metric("P-Value", f"{chi2_p:.6f}")
        with col3:
            st.metric("Degrees of Freedom", dof)
        
        if chi2_p < 0.05:
            st.success("**Significant association** between incident type and day of week")
        else:
            st.info("**No significant association** between incident type and day of week")
        
        # Display contingency table
        st.subheader("Contingency Table")
        st.dataframe(contingency_table, use_container_width=True)

def show_predictive_modeling_old(df):
    """Display predictive modeling interface"""
    
    st.subheader("🤖 Predictive Modeling")
    
    # Model selection
    model_type = st.selectbox(
        "Select Model Type:",
        ["Linear Regression", "Random Forest", "Time Series Forecast"]
    )
    
    if model_type in ["Linear Regression", "Random Forest"]:
        
        # Feature selection
        st.subheader("Target Variable")
        target_options = ['severity', 'Length_of_Time(Hours)', 'incidents_per_town_hour']
        target = st.selectbox("Select target variable to predict:", target_options)
        
        st.subheader("Feature Selection")
        feature_options = ['hour', 'type', 'is_weekend', 'morning_rush', 'evening_rush', 'location_numerical']
        available_features = [f for f in feature_options if f in df.columns]
        
        if not available_features:
            st.warning("No suitable features available for modeling")
            return
        
        selected_features = st.multiselect(
            "Select features for prediction:",
            available_features,
            default=available_features[:3]
        )
        
        if selected_features and target in df.columns:
            # Prepare data
            feature_df = df[selected_features + [target]].dropna()
            
            if len(feature_df) < 10:
                st.warning("Insufficient data for modeling (need at least 10 records)")
                return
            
            X = feature_df[selected_features]
            y = feature_df[target]
            
            # Train-test split
            test_size = st.slider("Test Set Size (%)", 10, 50, 20) / 100
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42)
            
            # Model training options
            use_cv = st.checkbox("Use Cross-Validation (Recommended)", value=True, 
                               help="Cross-validation provides more reliable performance estimates")
            
            if st.button("Train Model"):
                with st.spinner("Training model..."):
                    
                    if model_type == "Linear Regression":
                        model = LinearRegression()
                    else:  # Random Forest
                        model = RandomForestRegressor(n_estimators=100, random_state=42)
                    
                    if use_cv:
                        # Cross-validation approach (more robust)
                        cv_scores_r2 = cross_val_score(model, X, y, cv=5, scoring='r2')
                        cv_scores_rmse = -cross_val_score(model, X, y, cv=5, scoring='neg_root_mean_squared_error')
                        
                        # Train on full dataset for feature importance
                        model.fit(X, y)
                        
                        # Display cross-validation results
                        st.subheader("Cross-Validation Results (5-Fold)")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Mean CV R²", f"{cv_scores_r2.mean():.3f}")
                        with col2:
                            st.metric("R² Std Dev", f"{cv_scores_r2.std():.3f}")
                        with col3:
                            st.metric("Mean CV RMSE", f"{cv_scores_rmse.mean():.3f}")
                        with col4:
                            st.metric("RMSE Std Dev", f"{cv_scores_rmse.std():.3f}")
                        
                        # Show individual fold results
                        cv_results_df = pd.DataFrame({
                            'Fold': range(1, 6),
                            'R² Score': cv_scores_r2,
                            'RMSE': cv_scores_rmse
                        })
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            fig_cv_r2 = px.bar(cv_results_df, x='Fold', y='R² Score', 
                                             title="R² Scores by Fold")
                            st.plotly_chart(fig_cv_r2, use_container_width=True)
                        
                        with col2:
                            fig_cv_rmse = px.bar(cv_results_df, x='Fold', y='RMSE', 
                                               title="RMSE by Fold")
                            st.plotly_chart(fig_cv_rmse, use_container_width=True)
                            
                        st.info("💡 **Cross-validation provides more reliable estimates** by testing the model on multiple data splits")
                        
                    else:
                        # Traditional train-test split
                        model.fit(X_train, y_train)
                        
                        # Predictions
                        y_pred_train = model.predict(X_train)
                        y_pred_test = model.predict(X_test)
                        
                        # Metrics
                        train_r2 = r2_score(y_train, y_pred_train)
                        test_r2 = r2_score(y_test, y_pred_test)
                        train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
                        test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
                        
                        # Display results
                        st.subheader("Train-Test Split Results")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Train R²", f"{train_r2:.3f}")
                        with col2:
                            st.metric("Test R²", f"{test_r2:.3f}")
                        with col3:
                            st.metric("Train RMSE", f"{train_rmse:.3f}")
                        with col4:
                            st.metric("Test RMSE", f"{test_rmse:.3f}")
                        
                        # Prediction vs Actual plot (only for train-test split)
                        fig_pred = go.Figure()
                        fig_pred.add_trace(go.Scatter(
                            x=y_test, y=y_pred_test,
                            mode='markers',
                            name='Predictions',
                            marker=dict(color='#2d5016', size=8)
                        ))
                        fig_pred.add_trace(go.Scatter(
                            x=[y_test.min(), y_test.max()],
                            y=[y_test.min(), y_test.max()],
                            mode='lines',
                            name='Perfect Prediction',
                            line=dict(color='red', dash='dash')
                        ))
                        fig_pred.update_layout(
                            title="Predicted vs Actual Values",
                            xaxis_title="Actual",
                            yaxis_title="Predicted",
                            height=500
                        )
                        st.plotly_chart(fig_pred, use_container_width=True)
                    
                    # Feature importance (for Random Forest)
                    if model_type == "Random Forest":
                        st.subheader("Feature Importance")
                        importance_df = pd.DataFrame({
                            'feature': selected_features,
                            'importance': model.feature_importances_
                        }).sort_values('importance', ascending=False)
                        
                        fig_importance = px.bar(
                            importance_df,
                            x='importance',
                            y='feature',
                            orientation='h',
                            title="Feature Importance",
                            color_discrete_sequence=['#5a7c47']
                        )
                        st.plotly_chart(fig_importance, use_container_width=True)
    
    elif model_type == "Time Series Forecast":
        st.subheader("Time Series Forecasting")
        
        # Prepare time series data
        daily_incidents = df.groupby('date').size().reset_index(name='incident_count')
        daily_incidents['date'] = pd.to_datetime(daily_incidents['date'])
        daily_incidents = daily_incidents.sort_values('date')
        
        if len(daily_incidents) < 30:
            st.warning("Need at least 30 days of data for reliable time series forecasting")
            return
        
        st.info("**Simple Moving Average Forecast** - Undergraduate-friendly forecasting method")
        
        # Simple moving average forecast (undergraduate level)
        window_size = st.slider("Moving Average Window (days)", 3, 14, 7)
        forecast_days = st.slider("Forecast Period (days)", 1, 30, 7)
        
        if st.button("Generate Forecast"):
            with st.spinner("Generating forecast..."):
                
                # Calculate moving average
                daily_incidents['moving_avg'] = daily_incidents['incident_count'].rolling(window=window_size).mean()
                
                # Simple forecast using last moving average value
                last_ma = daily_incidents['moving_avg'].iloc[-1]
                
                # Create forecast dates
                last_date = daily_incidents['date'].max()
                forecast_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=forecast_days)
                
                # Simple forecast (constant based on moving average)
                forecast_values = [last_ma] * forecast_days
                
                # Calculate confidence intervals (simple approach)
                recent_residuals = daily_incidents['incident_count'].iloc[-window_size:] - daily_incidents['moving_avg'].iloc[-window_size:]
                forecast_std = np.std(recent_residuals.dropna())
                
                # Upper and lower bounds (95% confidence interval approximation)
                upper_bound = [val + 1.96 * forecast_std for val in forecast_values]
                lower_bound = [val - 1.96 * forecast_std for val in forecast_values]
                
                # Create forecast dataframe
                forecast_df = pd.DataFrame({
                    'date': forecast_dates,
                    'forecast': forecast_values,
                    'upper_bound': upper_bound,
                    'lower_bound': lower_bound
                })
                
                # Display forecast metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Forecast Mean", f"{np.mean(forecast_values):.1f}")
                with col2:
                    st.metric("Confidence Interval", f"±{1.96 * forecast_std:.1f}")
                with col3:
                    st.metric("Window Size", f"{window_size} days")
                
                # Plot historical data with forecast
                fig_forecast = go.Figure()
                
                # Historical data
                fig_forecast.add_trace(go.Scatter(
                    x=daily_incidents['date'],
                    y=daily_incidents['incident_count'],
                    mode='lines+markers',
                    name='Historical Data',
                    line=dict(color='#2d5016')
                ))
                
                # Moving average
                fig_forecast.add_trace(go.Scatter(
                    x=daily_incidents['date'],
                    y=daily_incidents['moving_avg'],
                    mode='lines',
                    name=f'{window_size}-Day Moving Average',
                    line=dict(color='#8b4513', dash='dash')
                ))
                
                # Forecast
                fig_forecast.add_trace(go.Scatter(
                    x=forecast_df['date'],
                    y=forecast_df['forecast'],
                    mode='lines+markers',
                    name='Forecast',
                    line=dict(color='#5a7c47')
                ))
                
                # Confidence interval
                fig_forecast.add_trace(go.Scatter(
                    x=forecast_df['date'],
                    y=forecast_df['upper_bound'],
                    mode='lines',
                    name='Upper 95% CI',
                    line=dict(color='#5a7c47', dash='dot'),
                    showlegend=False
                ))
                
                fig_forecast.add_trace(go.Scatter(
                    x=forecast_df['date'],
                    y=forecast_df['lower_bound'],
                    mode='lines',
                    name='95% Confidence Interval',
                    line=dict(color='#5a7c47', dash='dot'),
                    fill='tonexty',
                    fillcolor='rgba(45, 80, 22, 0.2)'
                ))
                
                fig_forecast.update_layout(
                    title="Traffic Incident Forecast",
                    xaxis_title="Date",
                    yaxis_title="Incidents per Day",
                    height=500,
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig_forecast, use_container_width=True)
                
                # Display forecast table
                st.subheader("📋 Forecast Summary")
                forecast_display = forecast_df.copy()
                forecast_display['date'] = forecast_display['date'].dt.strftime('%Y-%m-%d')
                forecast_display = forecast_display.round(1)
                st.dataframe(forecast_display, use_container_width=True)
                
                st.info("**Method**: Simple moving average with empirical confidence intervals. For advanced forecasting, consider ARIMA or exponential smoothing methods.")

def show_bias_detection_old(df):
    """Display bias detection analysis"""
    
    st.subheader("Bias Detection Analysis")
    st.markdown("Analyzing potential biases in traffic incident reporting and data collection")
    
    # Geographical bias
    st.subheader("Geographical Bias Analysis")
    
    location_incidents = df['location'].value_counts()
    location_population = {
        'Providence': 190934,
        'Warwick': 82823,
        'Cranston': 82934,
        'Pawtucket': 75604,
        # Add more as needed
    }
    
    if len(location_incidents) > 0:
        # Calc incidents/capita where population data available
        bias_data = []
        for location in location_incidents.index[:10]:  # Top 10 locations
            incidents = location_incidents[location]
            population = location_population.get(location, np.nan)
            
            bias_data.append({
                'location': location,
                'incidents': incidents,
                'population': population,
                'incidents_per_capita': incidents / population * 1000 if not np.isnan(population) else np.nan
            })
        
        bias_df = pd.DataFrame(bias_data)
        
        # Display raw vs /capita comparison
        col1, col2 = st.columns(2)
        
        with col1:
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.barplot(data=bias_df, x='location', y='incidents', ax=ax, color=VILLAGE_COLORS['primary'])
            ax.set_title("Raw Incident Counts", fontsize=14, fontweight='bold', color=VILLAGE_COLORS['primary'])
            ax.set_xlabel("Location", color=VILLAGE_COLORS['primary'])
            ax.set_ylabel("Incidents", color=VILLAGE_COLORS['primary'])
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()
        
        with col2:
            bias_df_filtered = bias_df.dropna(subset=['incidents_per_capita'])
            if not bias_df_filtered.empty:
                fig, ax = plt.subplots(figsize=(10, 6))
                sns.barplot(data=bias_df_filtered, x='location', y='incidents_per_capita', ax=ax, color=VILLAGE_COLORS['accent'])
                ax.set_title("Incidents per 1000 Residents", fontsize=14, fontweight='bold', color=VILLAGE_COLORS['primary'])
                ax.set_xlabel("Location", color=VILLAGE_COLORS['primary'])
                ax.set_ylabel("Incidents per 1000 Residents", color=VILLAGE_COLORS['primary'])
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()
                st.pyplot(fig)
                plt.close()
            else:
                st.info("Population data not available for per-capita analysis")
    
    # Temporal bias
    st.subheader("Temporal Bias Analysis")
    
    # Check for reporting patterns that might indicate bias
    hourly_reports = df.groupby('hour').size()
    
    # Expected uniform distribution
    expected_per_hour = len(df) / 24
    
    # Chi-square test for uniform distribution
    chi2_temporal, p_temporal = stats.chisquare(hourly_reports)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Chi-Square Statistic", f"{chi2_temporal:.2f}")
    with col2:
        st.metric("P-Value", f"{p_temporal:.6f}")
    
    if p_temporal < 0.05:
        st.warning("**Potential temporal bias detected** - Incident reporting varies significantly by hour")
    else:
        st.success("**No significant temporal bias** - Incident reporting appears consistent across hours")
    
    # Severity bias by location
    st.subheader("⚖️ Severity Reporting Bias")
    
    severity_by_location = df.groupby('location')['severity'].agg(['mean', 'std', 'count']).reset_index()
    severity_by_location = severity_by_location[severity_by_location['count'] >= 5]  # Minimum sample size
    
    if not severity_by_location.empty:
        # ANOVA test for severity differences
        location_groups = [df[df['location'] == loc]['severity'].dropna() 
                          for loc in severity_by_location['location']]
        
        f_stat_severity, p_severity = stats.f_oneway(*location_groups)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("F-Statistic", f"{f_stat_severity:.4f}")
        with col2:
            st.metric("P-Value", f"{p_severity:.6f}")
        
        if p_severity < 0.05:
            st.warning("**Potential severity bias** - Significant differences in reported severity across locations")
        else:
            st.success("**No significant severity bias** - Consistent severity reporting across locations")
        
        # Viz
        fig_severity_bias = px.box(
            df[df['location'].isin(severity_by_location['location'])],
            x='location',
            y='severity',
            title="Severity Distribution by Location",
            color_discrete_sequence=['#8b4513']
        )
        fig_severity_bias.update_xaxes(tickangle=45)
        st.plotly_chart(fig_severity_bias, use_container_width=True)
    
    # Data quality assessment
    st.subheader("Data Quality Assessment")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        missing_percentage = (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
        st.metric("Missing Data", f"{missing_percentage:.1f}%")
    
    with col2:
        duplicate_percentage = (df.duplicated().sum() / len(df)) * 100
        st.metric("Duplicate Records", f"{duplicate_percentage:.1f}%")
    
    with col3:
        # Check for outliers in duration
        Q1 = df['Length_of_Time(Hours)'].quantile(0.25)
        Q3 = df['Length_of_Time(Hours)'].quantile(0.75)
        IQR = Q3 - Q1
        outliers = df[(df['Length_of_Time(Hours)'] < (Q1 - 1.5 * IQR)) | 
                     (df['Length_of_Time(Hours)'] > (Q3 + 1.5 * IQR))]
        outlier_percentage = (len(outliers) / len(df)) * 100
        st.metric("Duration Outliers", f"{outlier_percentage:.1f}%")

if __name__ == "__main__":
    show()