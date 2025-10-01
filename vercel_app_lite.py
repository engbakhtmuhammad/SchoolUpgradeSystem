# Lightweight School Upgrade System for Vercel
import os
import sys
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from werkzeug.utils import secure_filename
import json
from datetime import datetime

# Set Vercel environment
os.environ['VERCEL'] = '1'

app = Flask(__name__)
app.secret_key = 'school_upgrade_secret_key_2025'

# Configure paths for Vercel
if os.environ.get('VERCEL'):
    app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
    app.config['DOWNLOAD_FOLDER'] = '/tmp/downloads'
else:
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['DOWNLOAD_FOLDER'] = 'downloads'

app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Ensure directories exist
for folder in [app.config['UPLOAD_FOLDER'], app.config['DOWNLOAD_FOLDER']]:
    try:
        os.makedirs(folder, exist_ok=True)
    except Exception:
        pass

# Global analyzer instance - will be initialized lazily
analyzer = None

def get_analyzer():
    """Lazy load the analyzer to avoid import issues during startup"""
    global analyzer
    if analyzer is None:
        try:
            # Import heavy dependencies only when needed
            import pandas as pd
            import numpy as np
            from geopy.distance import geodesic
            import folium
            from folium import plugins
            
            # Import the analyzer class from the original app
            from app import SchoolUpgradeAnalyzer
            analyzer = SchoolUpgradeAnalyzer()
        except Exception as e:
            # If imports fail, create a dummy analyzer
            class DummyAnalyzer:
                def __init__(self):
                    self.schools_df = None
                    self.error = str(e)
                    
                def load_data(self, *args, **kwargs):
                    return False, f"Failed to initialize analyzer: {self.error}"
            
            analyzer = DummyAnalyzer()
    return analyzer

@app.route('/')
def index():
    try:
        return render_template('index_elegant.html')
    except Exception as e:
        return jsonify({'error': 'Template error', 'message': str(e)}), 500

@app.route('/status')
def status():
    """Health check and system status"""
    try:
        # Test heavy imports
        import pandas as pd
        import numpy as np
        import folium
        from geopy.distance import geodesic
        
        return jsonify({
            'status': 'healthy',
            'python_version': sys.version,
            'pandas_version': pd.__version__,
            'numpy_version': np.__version__,
            'upload_folder': app.config['UPLOAD_FOLDER'],
            'download_folder': app.config['DOWNLOAD_FOLDER']
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'python_version': sys.version,
            'upload_folder': app.config['UPLOAD_FOLDER'],
            'download_folder': app.config['DOWNLOAD_FOLDER']
        }), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Try to load data using the analyzer
            analyzer_instance = get_analyzer()
            success, message = analyzer_instance.load_data(file_path)
            
            if success:
                flash(f"File uploaded successfully: {message}", 'success')
                return redirect(url_for('configure'))
            else:
                flash(f"Error processing file: {message}", 'error')
                
        return redirect(url_for('index'))
        
    except Exception as e:
        flash(f"Upload error: {str(e)}", 'error')
        return redirect(url_for('index'))

@app.route('/load-sample')
def load_sample():
    """Load sample data"""
    try:
        analyzer_instance = get_analyzer()
        
        # Try different locations for sample data
        possible_paths = [
            'balochistan_census.csv',
            'data/balochistan_census.csv',
            os.path.join(os.path.dirname(__file__), 'balochistan_census.csv'),
            os.path.join(os.path.dirname(__file__), 'data', 'balochistan_census.csv')
        ]
        
        file_path = None
        for path in possible_paths:
            if os.path.exists(path):
                file_path = path
                break
        
        if file_path:
            success, message = analyzer_instance.load_data(file_path)
            if success:
                flash(f"Sample data loaded: {message}", 'success')
                return redirect(url_for('configure'))
            else:
                flash(f"Error loading sample data: {message}", 'error')
        else:
            flash("Sample data file not found", 'error')
            
    except Exception as e:
        flash(f"Error: {str(e)}", 'error')
    
    return redirect(url_for('index'))

@app.route('/configure')
def configure():
    try:
        analyzer_instance = get_analyzer()
        if hasattr(analyzer_instance, 'error'):
            flash(f'System error: {analyzer_instance.error}', 'error')
            return redirect(url_for('index'))
            
        if analyzer_instance.schools_df is None or analyzer_instance.schools_df.empty:
            flash('Please upload data first', 'warning')
            return redirect(url_for('index'))
        
        return render_template('configure_elegant.html')
    except Exception as e:
        flash(f"Configuration error: {str(e)}", 'error')
        return redirect(url_for('index'))

# Add error handlers
@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'The application encountered an unexpected error'
    }), 500

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested resource was not found'
    }), 404

# For Vercel
application = app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5042))
    app.run(debug=False, host='0.0.0.0', port=port)
