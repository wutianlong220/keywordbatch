"""
Task Management System for Keyword Batch Processing
Handles job creation, execution, monitoring, and control
"""

import threading
import time
import json
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from enum import Enum

from services.file_processor import FileProcessor, ProcessingResult
from services.api_client import DeepSeekAPI, APIResult
from services.log_manager import log_manager, LogLevel, LogCategory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JobStatus(Enum):
    """Job status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class JobProgress:
    """Job progress tracking"""
    total_files: int = 0
    completed_files: int = 0
    failed_files: int = 0
    total_batches: int = 0
    completed_batches: int = 0
    failed_batches: int = 0
    total_keywords: int = 0
    processed_keywords: int = 0
    current_file: str = ""
    current_batch: int = 0
    processing_time: str = "0s"
    estimated_time_remaining: str = ""
    last_updated: str = ""


@dataclass
class Job:
    """Job data class"""
    job_id: str
    input_folder: str
    output_folder: str
    status: JobStatus = JobStatus.PENDING
    progress: JobProgress = None
    results: List[Dict[str, Any]] = None
    error_message: str = ""
    created_at: str = ""
    started_at: str = ""
    completed_at: str = ""
    config: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.progress is None:
            self.progress = JobProgress()
        if self.results is None:
            self.results = []
        if self.config is None:
            self.config = {}
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class TaskManager:
    """Task management system for batch processing"""
    
    def __init__(self):
        self.jobs: Dict[str, Job] = {}
        self.active_threads: Dict[str, threading.Thread] = {}
        self.stop_flags: Dict[str, bool] = {}
        self.pause_flags: Dict[str, bool] = {}
        self.lock = threading.Lock()
        
        logger.info("TaskManager initialized")
    
    def create_job(self, input_folder: str, output_folder: str, config: Dict[str, Any] = None) -> str:
        """
        Create a new batch processing job
        
        Args:
            input_folder: Path to input folder
            output_folder: Path to output folder
            config: Additional configuration
            
        Returns:
            Job ID
        """
        import time
        
        job_id = f"job_{int(time.time())}"
        
        job = Job(
            job_id=job_id,
            input_folder=input_folder,
            output_folder=output_folder,
            config=config or {}
        )
        
        with self.lock:
            self.jobs[job_id] = job
            self.stop_flags[job_id] = False
            self.pause_flags[job_id] = False
        
        logger.info(f"Created job {job_id} for folder {input_folder}")
        return job_id
    
    def start_job(self, job_id: str) -> bool:
        """
        Start a job execution
        
        Args:
            job_id: Job ID to start
            
        Returns:
            True if job was started successfully
        """
        with self.lock:
            if job_id not in self.jobs:
                logger.error(f"Job {job_id} not found")
                return False
            
            job = self.jobs[job_id]
            if job.status != JobStatus.PENDING:
                logger.error(f"Job {job_id} is not in PENDING status")
                return False
            
            job.status = JobStatus.RUNNING
            job.started_at = datetime.now().isoformat()
        
        # Start processing thread
        thread = threading.Thread(target=self._process_job, args=(job_id,))
        thread.daemon = True
        thread.start()
        
        with self.lock:
            self.active_threads[job_id] = thread
        
        logger.info(f"Started job {job_id}")
        log_manager.info(LogCategory.TASK_MANAGEMENT, f"Started job {job_id}", job_id=job_id)
        return True
    
    def pause_job(self, job_id: str) -> bool:
        """
        Pause a running job
        
        Args:
            job_id: Job ID to pause
            
        Returns:
            True if job was paused successfully
        """
        with self.lock:
            if job_id not in self.jobs:
                return False
            
            job = self.jobs[job_id]
            if job.status != JobStatus.RUNNING:
                return False
            
            job.status = JobStatus.PAUSED
            self.pause_flags[job_id] = True
        
        logger.info(f"Paused job {job_id}")
        log_manager.info(LogCategory.TASK_MANAGEMENT, f"Paused job {job_id}", job_id=job_id)
        return True
    
    def resume_job(self, job_id: str) -> bool:
        """
        Resume a paused job
        
        Args:
            job_id: Job ID to resume
            
        Returns:
            True if job was resumed successfully
        """
        with self.lock:
            if job_id not in self.jobs:
                return False
            
            job = self.jobs[job_id]
            if job.status != JobStatus.PAUSED:
                return False
            
            job.status = JobStatus.RUNNING
            self.pause_flags[job_id] = False
        
        logger.info(f"Resumed job {job_id}")
        return True
    
    def stop_job(self, job_id: str) -> bool:
        """
        Stop a job
        
        Args:
            job_id: Job ID to stop
            
        Returns:
            True if job was stopped successfully
        """
        with self.lock:
            if job_id not in self.jobs:
                return False
            
            job = self.jobs[job_id]
            if job.status not in [JobStatus.RUNNING, JobStatus.PAUSED]:
                return False
            
            job.status = JobStatus.CANCELLED
            self.stop_flags[job_id] = True
        
        logger.info(f"Stopped job {job_id}")
        return True
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job status and progress
        
        Args:
            job_id: Job ID
            
        Returns:
            Job status dictionary or None if not found
        """
        with self.lock:
            if job_id not in self.jobs:
                return None
            
            job = self.jobs[job_id]
            
            # Update progress timestamp
            job.progress.last_updated = datetime.now().isoformat()
            
            return {
                'job_id': job.job_id,
                'status': job.status.value,
                'progress': asdict(job.progress),
                'input_folder': job.input_folder,
                'output_folder': job.output_folder,
                'created_at': job.created_at,
                'started_at': job.started_at,
                'completed_at': job.completed_at,
                'error_message': job.error_message,
                'config': job.config
            }
    
    def get_job_results(self, job_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get job results
        
        Args:
            job_id: Job ID
            
        Returns:
            List of results or None if not found
        """
        with self.lock:
            if job_id not in self.jobs:
                return None
            
            return self.jobs[job_id].results
    
    def list_jobs(self) -> List[Dict[str, Any]]:
        """
        List all jobs
        
        Returns:
            List of job summaries
        """
        with self.lock:
            return [
                {
                    'job_id': job.job_id,
                    'status': job.status.value,
                    'input_folder': job.input_folder,
                    'output_folder': job.output_folder,
                    'created_at': job.created_at,
                    'progress': asdict(job.progress)
                }
                for job in self.jobs.values()
            ]
    
    def _process_job(self, job_id: str):
        """
        Internal method to process a job
        
        Args:
            job_id: Job ID to process
        """
        try:
            job = self.jobs[job_id]
            
            # Initialize processors
            file_processor = FileProcessor(job.input_folder, job.output_folder)
            api_client = DeepSeekAPI()
            
            # Scan for files
            excel_files = file_processor.scan_excel_files()
            
            with self.lock:
                job.progress.total_files = len(excel_files)
            
            # Process each file
            for file_idx, file_path in enumerate(excel_files):
                if self.stop_flags[job_id]:
                    break
                
                # Wait if paused
                while self.pause_flags[job_id] and not self.stop_flags[job_id]:
                    time.sleep(1)
                
                if self.stop_flags[job_id]:
                    break
                
                with self.lock:
                    job.progress.current_file = file_path.name
                
                logger.info(f"Processing file {file_idx + 1}/{len(excel_files)}: {file_path}")
                
                # Process file
                result, batches = file_processor.process_file(file_path)
                
                if not result.success:
                    with self.lock:
                        job.progress.failed_files += 1
                        job.results.append({
                            'file': str(file_path),
                            'status': 'failed',
                            'error': result.error_message
                        })
                    continue
                
                # Process batches
                with self.lock:
                    job.progress.total_batches += len(batches)
                    job.progress.total_keywords += result.processed_rows
                
                for batch_idx, batch in enumerate(batches):
                    if self.stop_flags[job_id]:
                        break
                    
                    # Wait if paused
                    while self.pause_flags[job_id] and not self.stop_flags[job_id]:
                        time.sleep(1)
                    
                    if self.stop_flags[job_id]:
                        break
                    
                    with self.lock:
                        job.progress.current_batch = batch_idx + 1
                    
                    # Process batch with API
                    translate = job.config.get('translate', True)
                    api_result = api_client.process_keyword_batch(batch, translate=translate)
                    
                    if api_result.success:
                        with self.lock:
                            job.progress.completed_batches += 1
                            job.progress.processed_keywords += len(api_result.data)
                            job.results.extend(api_result.data)
                    else:
                        with self.lock:
                            job.progress.failed_batches += 1
                            job.results.append({
                                'file': str(file_path),
                                'batch': batch_idx + 1,
                                'status': 'failed',
                                'error': api_result.error_message
                            })
                
                # Save processed data
                if not self.stop_flags[job_id]:
                    file_processor.save_processed_data(
                        [r for r in job.results if isinstance(r, dict) and 'keyword' in r],
                        f"processed_{file_path.stem}.xlsx"
                    )
                
                with self.lock:
                    job.progress.completed_files += 1
                    
                    # Update processing time
                    if job.started_at:
                        start_time = datetime.fromisoformat(job.started_at)
                        elapsed = datetime.now() - start_time
                        job.progress.processing_time = str(elapsed).split('.')[0]
                        
                        # Estimate remaining time
                        if job.progress.completed_files > 0:
                            avg_time_per_file = elapsed.total_seconds() / job.progress.completed_files
                            remaining_files = job.progress.total_files - job.progress.completed_files
                            remaining_seconds = avg_time_per_file * remaining_files
                            job.progress.estimated_time_remaining = f"{int(remaining_seconds // 60)}m {int(remaining_seconds % 60)}s"
            
            # Finalize job
            with self.lock:
                if self.stop_flags[job_id]:
                    job.status = JobStatus.CANCELLED
                elif job.progress.failed_files == len(excel_files):
                    job.status = JobStatus.FAILED
                    job.error_message = "All files failed to process"
                else:
                    job.status = JobStatus.COMPLETED
                
                job.completed_at = datetime.now().isoformat()
            
            logger.info(f"Completed job {job_id} with status {job.status.value}")
            
        except Exception as e:
            with self.lock:
                job = self.jobs[job_id]
                job.status = JobStatus.FAILED
                job.error_message = str(e)
                job.completed_at = datetime.now().isoformat()
            
            logger.error(f"Job {job_id} failed: {str(e)}")
        
        finally:
            with self.lock:
                if job_id in self.active_threads:
                    del self.active_threads[job_id]
                if job_id in self.stop_flags:
                    del self.stop_flags[job_id]
                if job_id in self.pause_flags:
                    del self.pause_flags[job_id]


# Global task manager instance
task_manager = TaskManager()