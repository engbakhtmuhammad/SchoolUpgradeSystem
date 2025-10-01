from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route('/')
def hello():
    return jsonify({
        'message': 'Hello from Vercel!',
        'python_version': os.sys.version,
        'environment': 'vercel' if os.environ.get('VERCEL') else 'local'
    })

@app.route('/test-imports')
def test_imports():
    results = {}
    
    try:
        import pandas as pd
        results['pandas'] = f'✓ {pd.__version__}'
    except Exception as e:
        results['pandas'] = f'✗ {str(e)}'
    
    try:
        import numpy as np
        results['numpy'] = f'✓ {np.__version__}'
    except Exception as e:
        results['numpy'] = f'✗ {str(e)}'
        
    try:
        import folium
        results['folium'] = f'✓ {folium.__version__}'
    except Exception as e:
        results['folium'] = f'✗ {str(e)}'
        
    try:
        from geopy.distance import geodesic
        results['geopy'] = '✓ imported'
    except Exception as e:
        results['geopy'] = f'✗ {str(e)}'
    
    return jsonify(results)

# For Vercel
application = app

if __name__ == '__main__':
    app.run(debug=True)
