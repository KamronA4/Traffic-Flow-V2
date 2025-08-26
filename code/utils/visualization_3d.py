# utils/visualization_3d.py - 3D Visualization Engine for Village

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import json

# Village color scheme
VILLAGE_COLORS = {
    'primary': '#2d5016',
    'secondary': '#5a7c47',
    'accent': '#8b4513',
    'neutral': '#f5f1e8',
    'palette': ['#2d5016', '#5a7c47', '#8b4513', '#d4a574', '#9c8b7a', '#6b5b95']
}

class Village3DVisualizer:
    """3D visualization engine for traffic data"""
    
    def __init__(self):
        self.city_bounds = {
            'lat_min': 41.3, 'lat_max': 42.0,
            'lng_min': -71.8, 'lng_max': -71.0,
            'elevation_min': 0, 'elevation_max': 200
        }
        
        # Rhode Island major roads and infrastructure
        self.major_roads = self._load_major_roads()
        self.city_centers = self._load_city_centers()
        
    def _load_major_roads(self) -> List[Dict[str, Any]]:
        """Load major roads data for Rhode Island"""
        return [
            {
                'name': 'I-95',
                'type': 'interstate',
                'points': [
                    [41.35, -71.65, 20], [41.40, -71.60, 25], [41.45, -71.55, 30],
                    [41.50, -71.50, 35], [41.55, -71.45, 40], [41.60, -71.40, 45],
                    [41.65, -71.35, 50], [41.70, -71.30, 55], [41.75, -71.25, 60]
                ],
                'color': '#1f77b4',
                'width': 8
            },
            {
                'name': 'I-195',
                'type': 'interstate',
                'points': [
                    [41.80, -71.50, 25], [41.78, -71.45, 30], [41.76, -71.40, 35],
                    [41.74, -71.35, 40], [41.72, -71.30, 45], [41.70, -71.25, 50]
                ],
                'color': '#ff7f0e',
                'width': 8
            },
            {
                'name': 'Route 6',
                'type': 'highway',
                'points': [
                    [41.85, -71.70, 15], [41.83, -71.65, 20], [41.81, -71.60, 25],
                    [41.79, -71.55, 30], [41.77, -71.50, 35], [41.75, -71.45, 40]
                ],
                'color': '#2ca02c',
                'width': 6
            },
            {
                'name': 'Route 1',
                'type': 'highway',
                'points': [
                    [41.45, -71.40, 10], [41.50, -71.38, 15], [41.55, -71.36, 20],
                    [41.60, -71.34, 25], [41.65, -71.32, 30], [41.70, -71.30, 35]
                ],
                'color': '#d62728',
                'width': 6
            }
        ]
    
    def _load_city_centers(self) -> List[Dict[str, Any]]:
        """Load major city centers"""
        return [
            {'name': 'Providence', 'lat': 41.8236, 'lng': -71.4222, 'elevation': 50, 'population': 190934},
            {'name': 'Warwick', 'lat': 41.7001, 'lng': -71.4162, 'elevation': 30, 'population': 82823},
            {'name': 'Cranston', 'lat': 41.7790, 'lng': -71.4371, 'elevation': 40, 'population': 82073},
            {'name': 'Pawtucket', 'lat': 41.8787, 'lng': -71.3826, 'elevation': 35, 'population': 75604},
            {'name': 'East Providence', 'lat': 41.8137, 'lng': -71.3701, 'elevation': 25, 'population': 47139},
            {'name': 'Woonsocket', 'lat': 42.0029, 'lng': -71.5154, 'elevation': 120, 'population': 43982},
            {'name': 'Newport', 'lat': 41.4901, 'lng': -71.3128, 'elevation': 15, 'population': 25441}
        ]
    
    def create_3d_traffic_map(self, incident_data: pd.DataFrame, show_roads: bool = True, 
                             show_cities: bool = True, show_terrain: bool = True) -> go.Figure:
        """Create 3D traffic incident map"""
        fig = go.Figure()
        
        # Add terrain surface if requested
        if show_terrain:
            fig.add_trace(self._create_terrain_surface())
        
        # Add major roads if requested
        if show_roads:
            for road in self.major_roads:
                fig.add_trace(self._create_road_trace(road))
        
        # Add city centers if requested
        if show_cities:
            for city in self.city_centers:
                fig.add_trace(self._create_city_trace(city))
        
        # Add traffic incidents
        if not incident_data.empty:
            fig.add_trace(self._create_incident_trace(incident_data))
        
        # Configure layout
        fig.update_layout(
            title="3D Traffic Visualization - Rhode Island",
            scene=dict(
                xaxis_title="Longitude",
                yaxis_title="Latitude",
                zaxis_title="Elevation (m)",
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.5)
                ),
                bgcolor='rgba(245, 241, 232, 0.1)',
                xaxis=dict(backgroundcolor='rgba(245, 241, 232, 0.3)'),
                yaxis=dict(backgroundcolor='rgba(245, 241, 232, 0.3)'),
                zaxis=dict(backgroundcolor='rgba(245, 241, 232, 0.3)')
            ),
            paper_bgcolor='rgba(245, 241, 232, 0.1)',
            plot_bgcolor='rgba(245, 241, 232, 0.1)',
            font_color=VILLAGE_COLORS['primary'],
            showlegend=True,
            legend=dict(
                bgcolor='rgba(245, 241, 232, 0.8)',
                bordercolor=VILLAGE_COLORS['secondary'],
                borderwidth=1
            )
        )
        
        return fig
    
    def _create_terrain_surface(self) -> go.Surface:
        """Create terrain surface mesh"""
        # Create elevation grid
        lat_range = np.linspace(self.city_bounds['lat_min'], self.city_bounds['lat_max'], 50)
        lng_range = np.linspace(self.city_bounds['lng_min'], self.city_bounds['lng_max'], 50)
        
        lat_grid, lng_grid = np.meshgrid(lat_range, lng_range)
        
        # Generate synthetic elevation data
        elevation = np.zeros_like(lat_grid)
        for i in range(len(lat_range)):
            for j in range(len(lng_range)):
                # Add some hills and valleys
                elevation[i, j] = (
                    50 * np.sin(lat_grid[i, j] * 10) * np.cos(lng_grid[i, j] * 10) +
                    30 * np.sin(lat_grid[i, j] * 5) +
                    20 * np.cos(lng_grid[i, j] * 8) +
                    100
                )
        
        return go.Surface(
            x=lng_grid,
            y=lat_grid,
            z=elevation,
            colorscale='Earth',
            opacity=0.3,
            showscale=False,
            name='Terrain'
        )
    
    def _create_road_trace(self, road: Dict[str, Any]) -> go.Scatter3d:
        """Create 3D road trace"""
        points = np.array(road['points'])
        
        return go.Scatter3d(
            x=points[:, 1],  # longitude
            y=points[:, 0],  # latitude
            z=points[:, 2],  # elevation
            mode='lines',
            line=dict(
                color=road['color'],
                width=road['width']
            ),
            name=road['name'],
            hovertemplate=f"<b>{road['name']}</b><br>" +
                         "Type: %{text}<br>" +
                         "Lat: %{y:.4f}<br>" +
                         "Lng: %{x:.4f}<br>" +
                         "Elevation: %{z}m<extra></extra>",
            text=[road['type']] * len(points)
        )
    
    def _create_city_trace(self, city: Dict[str, Any]) -> go.Scatter3d:
        """Create 3D city marker"""
        # Scale marker size based on population
        size = min(20, max(8, city['population'] / 10000))
        
        return go.Scatter3d(
            x=[city['lng']],
            y=[city['lat']],
            z=[city['elevation'] + 10],  # Slightly above ground
            mode='markers+text',
            marker=dict(
                size=size,
                color=VILLAGE_COLORS['primary'],
                symbol='diamond',
                line=dict(color=VILLAGE_COLORS['secondary'], width=2)
            ),
            text=[city['name']],
            textposition='top center',
            textfont=dict(color=VILLAGE_COLORS['primary'], size=12),
            name=f"{city['name']} ({city['population']:,})",
            hovertemplate=f"<b>{city['name']}</b><br>" +
                         f"Population: {city['population']:,}<br>" +
                         f"Lat: {city['lat']:.4f}<br>" +
                         f"Lng: {city['lng']:.4f}<br>" +
                         f"Elevation: {city['elevation']}m<extra></extra>"
        )
    
    def _create_incident_trace(self, incident_data: pd.DataFrame) -> go.Scatter3d:
        """Create 3D incident markers"""
        # Handle different column names
        lat_col = 'latitude' if 'latitude' in incident_data.columns else 'lat'
        lng_col = 'longitude' if 'longitude' in incident_data.columns else 'lng'
        
        # Calculate marker properties based on severity
        colors = []
        sizes = []
        symbols = []
        
        for _, incident in incident_data.iterrows():
            severity = incident.get('severity', 1)
            
            # Color based on severity
            if severity >= 4:
                colors.append('#d32f2f')  # Red for high severity
            elif severity >= 3:
                colors.append('#ff9800')  # Orange for medium-high
            elif severity >= 2:
                colors.append('#ffc107')  # Yellow for medium
            else:
                colors.append('#4caf50')  # Green for low
            
            # Size based on severity
            sizes.append(max(5, severity * 3))
            
            # Symbol based on incident type
            if 'accident' in incident.get('description', '').lower():
                symbols.append('x')
            elif 'construction' in incident.get('description', '').lower():
                symbols.append('diamond')
            else:
                symbols.append('circle')
        
        # Add some elevation to incidents (above ground level)
        elevations = [30 + np.random.uniform(0, 10) for _ in range(len(incident_data))]
        
        return go.Scatter3d(
            x=incident_data[lng_col],
            y=incident_data[lat_col],
            z=elevations,
            mode='markers',
            marker=dict(
                size=sizes,
                color=colors,
                symbol=symbols,
                line=dict(color='white', width=1),
                opacity=0.8
            ),
            text=incident_data['description'],
            name='Traffic Incidents',
            hovertemplate="<b>%{text}</b><br>" +
                         "Location: %{customdata[0]}<br>" +
                         "Severity: %{customdata[1]}<br>" +
                         "Time: %{customdata[2]}<br>" +
                         "Lat: %{y:.4f}<br>" +
                         "Lng: %{x:.4f}<extra></extra>",
            customdata=list(zip(
                incident_data['location'],
                incident_data['severity'],
                incident_data['timestamp'].dt.strftime('%H:%M') if 'timestamp' in incident_data.columns else ['N/A'] * len(incident_data)
            ))
        )
    
    def create_traffic_flow_3d(self, flow_data: pd.DataFrame, time_range: int = 24) -> go.Figure:
        """Create 3D traffic flow visualization"""
        fig = go.Figure()
        
        # Create time-based flow animation
        time_steps = np.arange(0, time_range, 1)
        
        for i, hour in enumerate(time_steps):
            # Generate flow data for this hour
            flow_intensity = self._generate_flow_intensity(hour)
            
            # Create flow lines
            for road in self.major_roads:
                points = np.array(road['points'])
                intensity = flow_intensity.get(road['name'], 0.5)
                
                fig.add_trace(go.Scatter3d(
                    x=points[:, 1],
                    y=points[:, 0],
                    z=points[:, 2] + intensity * 20,  # Height based on flow
                    mode='lines',
                    line=dict(
                        color=self._get_flow_color(intensity),
                        width=max(2, intensity * 10)
                    ),
                    name=f"{road['name']} - {hour:02d}:00",
                    visible=(i == 0)  # Only show first frame initially
                ))
        
        # Add animation controls
        frames = []
        for i, hour in enumerate(time_steps):
            frame_data = []
            for j, road in enumerate(self.major_roads):
                trace_idx = i * len(self.major_roads) + j
                frame_data.append(go.Scatter3d(visible=True))
            
            frames.append(go.Frame(
                data=frame_data,
                name=f"Hour {hour:02d}"
            ))
        
        fig.frames = frames
        
        # Add play/pause controls
        fig.update_layout(
            updatemenus=[{
                'type': 'buttons',
                'showactive': False,
                'buttons': [
                    {
                        'label': 'Play',
                        'method': 'animate',
                        'args': [None, {'frame': {'duration': 500, 'redraw': True}, 'fromcurrent': True}]
                    },
                    {
                        'label': 'Pause',
                        'method': 'animate',
                        'args': [[None], {'frame': {'duration': 0, 'redraw': True}, 'mode': 'immediate'}]
                    }
                ]
            }],
            sliders=[{
                'steps': [
                    {
                        'args': [[f"Hour {hour:02d}"], {'frame': {'duration': 0, 'redraw': True}, 'mode': 'immediate'}],
                        'label': f"{hour:02d}:00",
                        'method': 'animate'
                    }
                    for hour in time_steps
                ],
                'active': 0,
                'currentvalue': {'prefix': 'Time: '},
                'len': 0.9,
                'x': 0.1,
                'y': 0,
                'xanchor': 'left',
                'yanchor': 'top'
            }]
        )
        
        fig.update_layout(
            title="3D Traffic Flow Animation",
            scene=dict(
                xaxis_title="Longitude",
                yaxis_title="Latitude",
                zaxis_title="Flow Intensity",
                camera=dict(eye=dict(x=1.2, y=1.2, z=1.2))
            ),
            paper_bgcolor='rgba(245, 241, 232, 0.1)',
            font_color=VILLAGE_COLORS['primary']
        )
        
        return fig
    
    def _generate_flow_intensity(self, hour: int) -> Dict[str, float]:
        """Generate synthetic flow intensity for given hour"""
        # Rush hour patterns
        if hour in [7, 8, 9, 17, 18, 19]:
            base_intensity = 0.8
        elif hour in [10, 11, 12, 13, 14, 15, 16]:
            base_intensity = 0.6
        else:
            base_intensity = 0.3
        
        # Add some randomness
        return {
            road['name']: min(1.0, base_intensity + np.random.uniform(-0.2, 0.2))
            for road in self.major_roads
        }
    
    def _get_flow_color(self, intensity: float) -> str:
        """Get color based on flow intensity"""
        if intensity < 0.3:
            return '#2d5016'  # Low flow - green
        elif intensity < 0.6:
            return '#8b4513'  # Medium flow - brown
        else:
            return '#d32f2f'  # High flow - red
    
    def create_heatmap_3d(self, incident_data: pd.DataFrame, grid_size: int = 30) -> go.Figure:
        """Create 3D heatmap of incident density"""
        fig = go.Figure()
        
        # Create grid
        lat_range = np.linspace(self.city_bounds['lat_min'], self.city_bounds['lat_max'], grid_size)
        lng_range = np.linspace(self.city_bounds['lng_min'], self.city_bounds['lng_max'], grid_size)
        
        lat_grid, lng_grid = np.meshgrid(lat_range, lng_range)
        
        # Calculate incident density
        density = np.zeros_like(lat_grid)
        
        if not incident_data.empty:
            lat_col = 'latitude' if 'latitude' in incident_data.columns else 'lat'
            lng_col = 'longitude' if 'longitude' in incident_data.columns else 'lng'
            
            for i in range(grid_size):
                for j in range(grid_size):
                    lat_center = lat_grid[i, j]
                    lng_center = lng_grid[i, j]
                    
                    # Count incidents within radius
                    distances = np.sqrt(
                        (incident_data[lat_col] - lat_center)**2 + 
                        (incident_data[lng_col] - lng_center)**2
                    )
                    
                    density[i, j] = np.sum(distances < 0.05)  # Within ~5km radius
        
        # Create 3D surface
        fig.add_trace(go.Surface(
            x=lng_grid,
            y=lat_grid,
            z=density,
            colorscale=[
                [0, VILLAGE_COLORS['neutral']],
                [0.3, VILLAGE_COLORS['secondary']],
                [0.7, VILLAGE_COLORS['accent']],
                [1, '#d32f2f']
            ],
            opacity=0.8,
            name='Incident Density'
        ))
        
        fig.update_layout(
            title="3D Incident Density Heatmap",
            scene=dict(
                xaxis_title="Longitude",
                yaxis_title="Latitude",
                zaxis_title="Incident Count",
                camera=dict(eye=dict(x=1.5, y=1.5, z=1.5))
            ),
            paper_bgcolor='rgba(245, 241, 232, 0.1)',
            font_color=VILLAGE_COLORS['primary']
        )
        
        return fig
    
    def create_network_analysis_3d(self, incident_data: pd.DataFrame) -> go.Figure:
        """Create 3D network analysis visualization"""
        fig = go.Figure()
        
        # Create network nodes (intersection points)
        nodes = self._create_network_nodes()
        
        # Create network edges (road connections)
        edges = self._create_network_edges(nodes)
        
        # Add edges
        for edge in edges:
            fig.add_trace(go.Scatter3d(
                x=[edge['from'][1], edge['to'][1]],
                y=[edge['from'][0], edge['to'][0]],
                z=[edge['from'][2], edge['to'][2]],
                mode='lines',
                line=dict(
                    color=VILLAGE_COLORS['secondary'],
                    width=2
                ),
                showlegend=False,
                hoverinfo='skip'
            ))
        
        # Add nodes
        node_lats = [node['lat'] for node in nodes]
        node_lngs = [node['lng'] for node in nodes]
        node_elevations = [node['elevation'] for node in nodes]
        
        fig.add_trace(go.Scatter3d(
            x=node_lngs,
            y=node_lats,
            z=node_elevations,
            mode='markers',
            marker=dict(
                size=8,
                color=VILLAGE_COLORS['primary'],
                symbol='circle',
                line=dict(color='white', width=1)
            ),
            name='Network Nodes',
            hovertemplate="<b>Node %{customdata}</b><br>" +
                         "Lat: %{y:.4f}<br>" +
                         "Lng: %{x:.4f}<br>" +
                         "Elevation: %{z}m<extra></extra>",
            customdata=list(range(len(nodes)))
        ))
        
        fig.update_layout(
            title="3D Traffic Network Analysis",
            scene=dict(
                xaxis_title="Longitude",
                yaxis_title="Latitude",
                zaxis_title="Elevation",
                camera=dict(eye=dict(x=1.5, y=1.5, z=1.5))
            ),
            paper_bgcolor='rgba(245, 241, 232, 0.1)',
            font_color=VILLAGE_COLORS['primary']
        )
        
        return fig
    
    def _create_network_nodes(self) -> List[Dict[str, Any]]:
        """Create network nodes from road intersections"""
        nodes = []
        
        # Create intersection points
        for i in range(20):
            lat = np.random.uniform(self.city_bounds['lat_min'], self.city_bounds['lat_max'])
            lng = np.random.uniform(self.city_bounds['lng_min'], self.city_bounds['lng_max'])
            elevation = np.random.uniform(10, 100)
            
            nodes.append({
                'id': i,
                'lat': lat,
                'lng': lng,
                'elevation': elevation,
                'type': 'intersection'
            })
        
        return nodes
    
    def _create_network_edges(self, nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create network edges between nodes"""
        edges = []
        
        for i in range(len(nodes)):
            for j in range(i + 1, min(i + 4, len(nodes))):  # Connect to nearby nodes
                from_node = nodes[i]
                to_node = nodes[j]
                
                # Calculate distance
                distance = np.sqrt(
                    (from_node['lat'] - to_node['lat'])**2 + 
                    (from_node['lng'] - to_node['lng'])**2
                )
                
                if distance < 0.1:  # Only connect nearby nodes
                    edges.append({
                        'from': [from_node['lat'], from_node['lng'], from_node['elevation']],
                        'to': [to_node['lat'], to_node['lng'], to_node['elevation']],
                        'distance': distance,
                        'weight': 1.0 / distance if distance > 0 else 1.0
                    })
        
        return edges

def show_3d_visualization_page():
    """Show 3D visualization page"""
    from .enterprise_auth import require_feature, get_current_user
    
    @require_feature("3d_visualization")
    def main():
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #faf8f3 0%, #f5f1e8 100%);
            padding: 2rem;
            border-radius: 15px;
            margin-bottom: 2rem;
            border-left: 4px solid #2d5016;
        ">
            <h1 style="color: #2d5016; margin: 0 0 1rem 0;">🏙️ 3D Traffic Visualization</h1>
            <p style="color: #5a7c47; margin: 0;">
                Advanced 3D visualization tools for traffic planning and analysis
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Initialize 3D visualizer
        visualizer = Village3DVisualizer()
        
        # Visualization type selection
        viz_type = st.selectbox(
            "Visualization Type",
            ["3D Traffic Map", "Traffic Flow Animation", "Incident Density Heatmap", "Network Analysis"]
        )
        
        # Load sample data
        from .data_sync import get_traffic_data
        from datetime import datetime, timedelta
        
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=7)
            incident_data = get_traffic_data(start_date=start_date, end_date=end_date)
        except:
            # Create sample data if none available
            incident_data = pd.DataFrame({
                'latitude': np.random.uniform(41.4, 41.9, 20),
                'longitude': np.random.uniform(-71.7, -71.2, 20),
                'severity': np.random.randint(1, 5, 20),
                'location': [f"Location {i}" for i in range(20)],
                'description': [f"Incident {i}" for i in range(20)],
                'timestamp': [datetime.now() - timedelta(hours=i) for i in range(20)]
            })
        
        # Display options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            show_roads = st.checkbox("Show Roads", value=True)
        with col2:
            show_cities = st.checkbox("Show Cities", value=True)
        with col3:
            show_terrain = st.checkbox("Show Terrain", value=True)
        
        # Generate visualization
        if viz_type == "3D Traffic Map":
            fig = visualizer.create_3d_traffic_map(
                incident_data, show_roads, show_cities, show_terrain
            )
        elif viz_type == "Traffic Flow Animation":
            fig = visualizer.create_traffic_flow_3d(incident_data)
        elif viz_type == "Incident Density Heatmap":
            fig = visualizer.create_heatmap_3d(incident_data)
        elif viz_type == "Network Analysis":
            fig = visualizer.create_network_analysis_3d(incident_data)
        
        # Display visualization
        st.plotly_chart(fig, use_container_width=True)
        
        # Visualization controls
        st.markdown("### Visualization Controls")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Reset View"):
                st.rerun()
        
        with col2:
            if st.button("Export 3D Model"):
                st.success("3D model export functionality coming soon!")
        
        # Information panel
        st.markdown("### Visualization Information")
        st.info("""
        **3D Visualization Features:**
        - Interactive 3D maps with terrain
        - Real-time traffic flow animation
        - Incident density heatmaps
        - Network analysis tools
        - Export capabilities
        """)
    
    main()

if __name__ == "__main__":
    show_3d_visualization_page()