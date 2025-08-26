#!/usr/bin/env python3
"""
Traffic Data API - REST endpoints for remote data access
Provides secure API endpoints for Streamlit application to access VM-collected data
"""

import os
import sys
import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
import pandas as pd
from functools import wraps
import jwt
import hashlib

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

app = Flask(__name__)
CORS(app)

# Configuration
API_SECRET_KEY = os.getenv('API_SECRET_KEY', 'your-secret-key-change-in-production')
DB_PATH = os.getenv('DB_PATH', '/var/lib/traffic-collector/traffic_data.db')
API_KEY = os.getenv('TRAFFIC_API_KEY', 'your-api-key-change-in-production')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def require_api_key(f):
    """Decorator to require API key for endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        if not api_key or api_key != API_KEY:
            abort(401, description="Invalid or missing API key")
        return f(*args, **kwargs)
    return decorated_function

def get_db_connection():
    """Get database connection with error handling"""
    try:
        if not os.path.exists(DB_PATH):
            logger.error(f"Database not found at {DB_PATH}")
            return None
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'status': 'unhealthy', 'error': 'Database unavailable'}), 503
        
        conn.close()
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': 'connected'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 503

@app.route('/status')
@require_api_key
def status():
    """Get service status and statistics"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database unavailable'}), 503
        
        cursor = conn.cursor()
        
        # Get record counts
        cursor.execute("SELECT COUNT(*) FROM traffic_incidents")
        incidents_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM traffic_flow")
        flow_count = cursor.fetchone()[0]
        
        # Get API usage today
        today = datetime.now().date()
        cursor.execute("SELECT SUM(requests_count) FROM api_usage WHERE DATE(timestamp) = ?", (today,))
        api_usage_result = cursor.fetchone()
        api_usage = api_usage_result[0] if api_usage_result[0] else 0
        
        # Get latest collection time
        cursor.execute("SELECT MAX(collection_time) FROM traffic_incidents")
        latest_incident = cursor.fetchone()[0]
        
        cursor.execute("SELECT MAX(collection_time) FROM traffic_flow")
        latest_flow = cursor.fetchone()[0]
        
        # Get collection statistics for today
        cursor.execute("""
            SELECT zone_name, COUNT(*) as collections, AVG(records_collected) as avg_records
            FROM collection_stats 
            WHERE DATE(timestamp) = ? AND success = 1
            GROUP BY zone_name
        """, (today,))
        zone_stats = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'incidents_total': incidents_count,
            'flow_records_total': flow_count,
            'api_requests_today': api_usage,
            'latest_incident_collection': latest_incident,
            'latest_flow_collection': latest_flow,
            'zone_statistics': zone_stats,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Status endpoint error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/incidents')
@require_api_key
def get_incidents():
    """Get traffic incidents with optional filtering"""
    try:
        # Parse query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = int(request.args.get('limit', 1000))
        severity_min = request.args.get('severity_min', type=int)
        bbox = request.args.get('bbox')  # Format: lat1,lng1,lat2,lng2
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database unavailable'}), 503
        
        cursor = conn.cursor()
        
        # Build query
        query = """
            SELECT id, external_id, timestamp, collection_time, 
                   latitude, longitude, location, description, 
                   severity, incident_type, delay_minutes, data_source
            FROM traffic_incidents WHERE 1=1
        """
        params = []
        
        if start_date:
            query += " AND DATE(timestamp) >= ?"
            params.append(start_date)
            
        if end_date:
            query += " AND DATE(timestamp) <= ?"
            params.append(end_date)
            
        if severity_min:
            query += " AND severity >= ?"
            params.append(severity_min)
            
        if bbox:
            try:
                lat1, lng1, lat2, lng2 = map(float, bbox.split(','))
                query += " AND latitude BETWEEN ? AND ? AND longitude BETWEEN ? AND ?"
                params.extend([min(lat1, lat2), max(lat1, lat2), min(lng1, lng2), max(lng1, lng2)])
            except ValueError:
                return jsonify({'error': 'Invalid bbox format. Use: lat1,lng1,lat2,lng2'}), 400
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        incidents = []
        for row in rows:
            incident = dict(row)
            # Add derived fields for compatibility
            incident['date'] = datetime.fromisoformat(incident['timestamp']).date().isoformat()
            incident['hour'] = datetime.fromisoformat(incident['timestamp']).hour
            incident['lat'] = incident['latitude']
            incident['lng'] = incident['longitude']
            incidents.append(incident)
        
        conn.close()
        
        return jsonify({
            'incidents': incidents,
            'count': len(incidents),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Incidents endpoint error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/flow')
@require_api_key
def get_flow_data():
    """Get traffic flow data with optional filtering"""
    try:
        # Parse query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = int(request.args.get('limit', 1000))
        congestion_min = request.args.get('congestion_min', type=int)
        bbox = request.args.get('bbox')
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database unavailable'}), 503
        
        cursor = conn.cursor()
        
        # Build query
        query = """
            SELECT id, timestamp, collection_time, latitude, longitude, 
                   location, current_speed_mph, free_flow_speed_mph, 
                   confidence_level, congestion_level, data_source
            FROM traffic_flow WHERE 1=1
        """
        params = []
        
        if start_date:
            query += " AND DATE(timestamp) >= ?"
            params.append(start_date)
            
        if end_date:
            query += " AND DATE(timestamp) <= ?"
            params.append(end_date)
            
        if congestion_min:
            query += " AND congestion_level >= ?"
            params.append(congestion_min)
            
        if bbox:
            try:
                lat1, lng1, lat2, lng2 = map(float, bbox.split(','))
                query += " AND latitude BETWEEN ? AND ? AND longitude BETWEEN ? AND ?"
                params.extend([min(lat1, lat2), max(lat1, lat2), min(lng1, lng2), max(lng1, lng2)])
            except ValueError:
                return jsonify({'error': 'Invalid bbox format. Use: lat1,lng1,lat2,lng2'}), 400
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        flow_data = []
        for row in rows:
            flow_record = dict(row)
            # Add derived fields for compatibility
            flow_record['date'] = datetime.fromisoformat(flow_record['timestamp']).date().isoformat()
            flow_record['hour'] = datetime.fromisoformat(flow_record['timestamp']).hour
            flow_record['lat'] = flow_record['latitude']
            flow_record['lng'] = flow_record['longitude']
            flow_data.append(flow_record)
        
        conn.close()
        
        return jsonify({
            'flow_data': flow_data,
            'count': len(flow_data),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Flow endpoint error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/analytics/summary')
@require_api_key
def analytics_summary():
    """Get analytics summary for dashboard"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database unavailable'}), 503
        
        cursor = conn.cursor()
        
        # Get incident counts by severity
        cursor.execute("""
            SELECT severity, COUNT(*) as count
            FROM traffic_incidents 
            WHERE DATE(timestamp) >= DATE('now', '-7 days')
            GROUP BY severity
            ORDER BY severity
        """)
        severity_stats = [dict(row) for row in cursor.fetchall()]
        
        # Get hourly incident patterns
        cursor.execute("""
            SELECT strftime('%H', timestamp) as hour, COUNT(*) as count
            FROM traffic_incidents 
            WHERE DATE(timestamp) >= DATE('now', '-7 days')
            GROUP BY hour
            ORDER BY hour
        """)
        hourly_patterns = [dict(row) for row in cursor.fetchall()]
        
        # Get average speeds by zone
        cursor.execute("""
            SELECT location, AVG(current_speed_mph) as avg_speed, 
                   AVG(congestion_level) as avg_congestion
            FROM traffic_flow 
            WHERE DATE(timestamp) >= DATE('now', '-1 days')
            GROUP BY location
        """)
        zone_performance = [dict(row) for row in cursor.fetchall()]
        
        # Get collection efficiency
        cursor.execute("""
            SELECT DATE(timestamp) as date, 
                   COUNT(*) as collections,
                   AVG(records_collected) as avg_records,
                   AVG(collection_duration_seconds) as avg_duration
            FROM collection_stats 
            WHERE DATE(timestamp) >= DATE('now', '-7 days') AND success = 1
            GROUP BY DATE(timestamp)
            ORDER BY date
        """)
        collection_efficiency = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'severity_distribution': severity_stats,
            'hourly_patterns': hourly_patterns,
            'zone_performance': zone_performance,
            'collection_efficiency': collection_efficiency,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Analytics summary error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/zones')
@require_api_key
def get_zones():
    """Get configured collection zones with their statistics"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database unavailable'}), 503
        
        cursor = conn.cursor()
        
        # Get zone statistics
        cursor.execute("""
            SELECT zone_name, 
                   COUNT(*) as total_collections,
                   AVG(records_collected) as avg_records,
                   MAX(timestamp) as last_collection,
                   SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as success_rate
            FROM collection_stats 
            WHERE DATE(timestamp) >= DATE('now', '-7 days')
            GROUP BY zone_name
        """)
        zone_stats = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'zones': zone_stats,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Zones endpoint error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/export/<data_type>')
@require_api_key
def export_data(data_type):
    """Export data in various formats (CSV, JSON)"""
    try:
        if data_type not in ['incidents', 'flow', 'analytics']:
            return jsonify({'error': 'Invalid data type. Use: incidents, flow, analytics'}), 400
        
        format_type = request.args.get('format', 'json').lower()
        if format_type not in ['json', 'csv']:
            return jsonify({'error': 'Invalid format. Use: json, csv'}), 400
        
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = int(request.args.get('limit', 10000))
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database unavailable'}), 503
        
        if data_type == 'incidents':
            query = """
                SELECT * FROM traffic_incidents 
                WHERE 1=1
            """
            params = []
            
            if start_date:
                query += " AND DATE(timestamp) >= ?"
                params.append(start_date)
            if end_date:
                query += " AND DATE(timestamp) <= ?"
                params.append(end_date)
                
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
        elif data_type == 'flow':
            query = """
                SELECT * FROM traffic_flow 
                WHERE 1=1
            """
            params = []
            
            if start_date:
                query += " AND DATE(timestamp) >= ?"
                params.append(start_date)
            if end_date:
                query += " AND DATE(timestamp) <= ?"
                params.append(end_date)
                
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        if format_type == 'csv':
            from io import StringIO
            import csv
            
            output = StringIO()
            df.to_csv(output, index=False)
            
            from flask import Response
            return Response(
                output.getvalue(),
                mimetype="text/csv",
                headers={"Content-disposition": f"attachment; filename={data_type}_export.csv"}
            )
        else:
            return jsonify({
                'data': df.to_dict('records'),
                'count': len(df),
                'export_timestamp': datetime.now().isoformat()
            })
        
    except Exception as e:
        logger.error(f"Export endpoint error: {e}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Development server
    app.run(host='0.0.0.0', port=8080, debug=False)