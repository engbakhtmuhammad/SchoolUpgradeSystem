from flask import Flask, jsonify, render_template
import os
import sys

app = Flask(__name__)
app.secret_key = 'school_upgrade_secret_key_2025'

# Set up directories
if os.environ.get('VERCEL'):
    app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
    app.config['DOWNLOAD_FOLDER'] = '/tmp/downloads'
else:
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['DOWNLOAD_FOLDER'] = 'downloads'

# Create directories
for folder in [app.config['UPLOAD_FOLDER'], app.config['DOWNLOAD_FOLDER']]:
    try:
        os.makedirs(folder, exist_ok=True)
    except:
        pass

@app.route('/')
def index():
    return jsonify({
        'status': 'School Upgrade System is running!',
        'environment': 'Vercel' if os.environ.get('VERCEL') else 'Local',
        'python_version': sys.version,
        'upload_folder': app.config['UPLOAD_FOLDER']
    })

@app.route('/test-heavy-imports')
def test_imports():
    """Test if heavy dependencies can be imported"""
    results = {}
    
    try:
        import pandas as pd
        results['pandas'] = f'✅ Success - Version: {pd.__version__}'
    except Exception as e:
        results['pandas'] = f'❌ Error: {str(e)}'
    
    try:
        import numpy as np  
        results['numpy'] = f'✅ Success - Version: {np.__version__}'
    except Exception as e:
        results['numpy'] = f'❌ Error: {str(e)}'
        
    try:
        import folium
        results['folium'] = f'✅ Success - Version: {folium.__version__}'
    except Exception as e:
        results['folium'] = f'❌ Error: {str(e)}'
        
    try:
        from geopy.distance import geodesic
        results['geopy'] = '✅ Success - Imported geodesic'
    except Exception as e:
        results['geopy'] = f'❌ Error: {str(e)}'
    
    return jsonify(results)

@app.route('/basic-page')
def basic_page():
    """Test template rendering"""
    try:
        return render_template('index_elegant.html')
    except Exception as e:
        return jsonify({
            'error': 'Template not found',
            'message': str(e),
            'available_templates': os.listdir('templates') if os.path.exists('templates') else []
        })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

# This is what Vercel will use
application = app

if __name__ == '__main__':
    app.run(debug=True, port=5000)
