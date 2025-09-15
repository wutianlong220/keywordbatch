"""
Keyword Batch Processing Application
Main Flask application
"""

import os
import sys
import time
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import Config
from services.task_manager import task_manager
from services.log_manager import log_manager, LogLevel, LogCategory
from services.config_manager import config_manager


def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    
    # Configure Flask app
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['MAX_CONTENT_LENGTH'] = Config.MAX_FILE_SIZE
    
    # Configure CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:5000", "http://127.0.0.1:5000"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Initialize configuration
    Config.init()
    
    return app


app = create_app()


@app.route('/')
def index():
    """Main page route"""
    return render_template('index.html')


@app.route('/progress')
def progress():
    """Progress page route"""
    return render_template('progress.html')


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """File upload endpoint"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # TODO: Implement file processing logic
    return jsonify({'message': 'File uploaded successfully', 'filename': file.filename})


@app.route('/api/batch-process', methods=['POST'])
def batch_process():
    """Batch processing endpoint"""
    try:
        data = request.get_json()
        
        input_folder = data.get('input_folder')
        output_folder = data.get('output_folder')
        config = data.get('config', {})
        
        if not input_folder or not output_folder:
            return jsonify({'error': 'Input and output folders are required'}), 400
        
        # Create and start job
        job_id = task_manager.create_job(input_folder, output_folder, config)
        
        if task_manager.start_job(job_id):
            return jsonify({
                'status': 'started',
                'message': 'Batch processing started',
                'job_id': job_id,
                'input_folder': input_folder,
                'output_folder': output_folder
            })
        else:
            return jsonify({'error': 'Failed to start job'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/job-status/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get batch processing job status"""
    status = task_manager.get_job_status(job_id)
    
    if status is None:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify(status)


@app.route('/api/job-control/<job_id>', methods=['POST'])
def job_control(job_id):
    """Control batch processing job (pause/resume/stop)"""
    try:
        data = request.get_json()
        action = data.get('action')  # 'pause', 'resume', 'stop'
        
        if action not in ['pause', 'resume', 'stop']:
            return jsonify({'error': 'Invalid action'}), 400
        
        # Execute the requested action
        success = False
        if action == 'pause':
            success = task_manager.pause_job(job_id)
        elif action == 'resume':
            success = task_manager.resume_job(job_id)
        elif action == 'stop':
            success = task_manager.stop_job(job_id)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': f'Job {action}ed successfully',
                'job_id': job_id,
                'action': action
            })
        else:
            return jsonify({'error': f'Failed to {action} job'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/job-results/<job_id>', methods=['GET'])
def get_job_results(job_id):
    """Get job results"""
    results = task_manager.get_job_results(job_id)
    
    if results is None:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify({
        'job_id': job_id,
        'results': results
    })


@app.route('/api/jobs', methods=['GET'])
def list_jobs():
    """List all jobs"""
    jobs = task_manager.list_jobs()
    return jsonify({
        'jobs': jobs,
        'total': len(jobs)
    })


@app.route('/api/stream-progress/<job_id>', methods=['GET'])
def stream_progress(job_id):
    """Long polling endpoint for real-time progress updates"""
    import time

    start_time = time.time()
    timeout = 30  # 30 seconds timeout

    while time.time() - start_time < timeout:
        status = task_manager.get_job_status(job_id)
        if status is None:
            return jsonify({'error': 'Job not found'}), 404

        # Check if there are updates
        if 'last_update' not in request.args or status['progress']['last_updated'] > request.args.get('last_update', ''):
            return jsonify(status)

        # Wait before checking again
        time.sleep(0.5)

    # Timeout reached, return current status
    return jsonify(status)


@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Get system logs"""
    level = request.args.get('level')
    category = request.args.get('category')
    job_id = request.args.get('job_id')
    limit = int(request.args.get('limit', 50))

    # Parse parameters
    log_level = None
    if level:
        log_level = LogLevel(level)

    log_category = None
    if category:
        log_category = LogCategory(category)

    logs = log_manager.get_logs(
        level=log_level,
        category=log_category,
        job_id=job_id,
        limit=limit
    )

    return jsonify({
        'logs': logs,
        'total': len(logs)
    })


@app.route('/api/logs/export', methods=['POST'])
def export_logs():
    """Export logs to file"""
    try:
        data = request.get_json()
        filename = data.get('filename', 'logs_export')
        format = data.get('format', 'json')

        if log_manager.export_logs(filename, format):
            return jsonify({
                'status': 'success',
                'message': f'Logs exported to {filename}.{format}'
            })
        else:
            return jsonify({'error': 'Failed to export logs'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/config', methods=['GET'])
def get_config():
    """Get application configuration"""
    try:
        config = config_manager.get_config()
        return jsonify({
            'config': config.__dict__,
            'summary': config_manager.get_config_summary(),
            'validation': config_manager.validate_config()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/config', methods=['POST'])
def update_config():
    """Update application configuration"""
    try:
        data = request.get_json()

        if config_manager.update_config(**data):
            log_manager.info(LogCategory.USER_INTERFACE, "Configuration updated")
            return jsonify({
                'status': 'success',
                'message': 'Configuration updated successfully'
            })
        else:
            return jsonify({'error': 'Failed to update configuration'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/config/reset', methods=['POST'])
def reset_config():
    """Reset configuration to defaults"""
    try:
        if config_manager.reset_config():
            log_manager.info(LogCategory.USER_INTERFACE, "Configuration reset to defaults")
            return jsonify({
                'status': 'success',
                'message': 'Configuration reset to defaults'
            })
        else:
            return jsonify({'error': 'Failed to reset configuration'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/config/export', methods=['POST'])
def export_config():
    """Export configuration to file"""
    try:
        data = request.get_json()
        filename = data.get('filename', 'config_export')
        format = data.get('format', 'json')

        if config_manager.export_config(filename, format):
            return jsonify({
                'status': 'success',
                'message': f'Configuration exported to {filename}.{format}'
            })
        else:
            return jsonify({'error': 'Failed to export configuration'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/config/import', methods=['POST'])
def import_config():
    """Import configuration from file"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Save uploaded file temporarily
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
            file.save(tmp_file.name)

        # Import configuration
        if config_manager.import_config(tmp_file.name):
            log_manager.info(LogCategory.USER_INTERFACE, f"Configuration imported from {file.filename}")
            return jsonify({
                'status': 'success',
                'message': 'Configuration imported successfully'
            })
        else:
            return jsonify({'error': 'Failed to import configuration'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    return jsonify({'error': 'File too large'}), 413


@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors"""
    return render_template('500.html'), 500


if __name__ == "__main__":
    print("Starting Keyword Batch Processing Application...")
    print(f"Project root: {project_root}")
    print(f"Config loaded: {Config.DEBUG}")
    
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG,
        threaded=True
    )