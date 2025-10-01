# Vercel-optimized School Upgrade System
import os

# Configure environment
os.environ['VERCEL'] = '1'

def create_application():
    """Create Flask application with error handling"""
    from flask import Flask, jsonify, render_template
    
    app = Flask(__name__)
    app.secret_key = 'school_upgrade_secret_key_2025'
    
    # Configure for Vercel
    app.config['UPLOAD_FOLDER'] = '/tmp/uploads' if os.environ.get('VERCEL') else 'uploads'
    app.config['DOWNLOAD_FOLDER'] = '/tmp/downloads' if os.environ.get('VERCEL') else 'downloads'
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
    
    # Ensure directories exist
    for folder in [app.config['UPLOAD_FOLDER'], app.config['DOWNLOAD_FOLDER']]:
        try:
            os.makedirs(folder, exist_ok=True)
        except Exception:
            pass
    
    # Basic health check route
    @app.route('/health')
    def health():
        return jsonify({
            'status': 'healthy',
            'environment': 'vercel' if os.environ.get('VERCEL') else 'local',
            'upload_folder': app.config['UPLOAD_FOLDER']
        })
    
    try:
        # Try to import the full application
        from app import app as original_app
        
        # Transfer configuration
        original_app.config.update(app.config)
        
        # Add our health check to the original app
        original_app.add_url_rule('/health', 'health', health)
        
        return original_app
        
    except Exception as e:
        # Fallback to basic app if import fails
        @app.route('/')
        def index():
            return render_template('index_elegant.html') if os.path.exists('templates/index_elegant.html') else jsonify({
                'error': 'Application initialization failed',
                'message': str(e),
                'note': 'This is a fallback response. Please check the logs.'
            })
        
        @app.route('/debug')
        def debug():
            import sys
            import traceback
            return jsonify({
                'error': str(e),
                'traceback': traceback.format_exc(),
                'python_version': sys.version,
                'working_directory': os.getcwd(),
                'files_in_directory': os.listdir('.'),
                'environment_vars': dict(os.environ)
            })
        
        return app

# Create the application
application = create_application()

if __name__ == '__main__':
    application.run(debug=True)