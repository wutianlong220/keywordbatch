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