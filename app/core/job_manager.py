"""
Job Manager
Handles database operations for jobs
"""

import sqlite3
from datetime import datetime
from pathlib import Path
import logging
import json

logger = logging.getLogger(__name__)

# Database path
DB_PATH = Path(__file__).parent.parent.parent / "jobs.db"


class JobManager:
    """Manage job records in database"""
    
    def __init__(self):
        self.db_path = DB_PATH
        self._init_db()
    
    def _init_db(self):
        """Initialize database if it doesn't exist"""
        if not self.db_path.exists():
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS jobs (
                        id TEXT PRIMARY KEY,
                        pipeline_name TEXT NOT NULL,
                        user_id TEXT,
                        status TEXT DEFAULT 'pending',
                        parameters TEXT,
                        results TEXT,
                        error_message TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        started_at TIMESTAMP,
                        completed_at TIMESTAMP,
                        execution_time REAL
                    )
                ''')
                conn.commit()
                logger.info(f"✅ Database initialized at: {self.db_path}")
    
    def create_job(self, pipeline_name: str, user_id: str = None, parameters: dict = None) -> dict:
        """Create a new job record"""
        
        import uuid
        job_id = str(uuid.uuid4())
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO jobs 
                (id, pipeline_name, user_id, parameters, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                job_id,
                pipeline_name,
                user_id or "anonymous",
                json.dumps(parameters) if parameters else "{}",
                "pending"
            ))
            conn.commit()
        
        logger.info(f"✅ Job created: {job_id}")
        return self.get_job(job_id)
    
    def get_job(self, job_id: str) -> dict:
        """Get job details"""
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                'SELECT * FROM jobs WHERE id = ?',
                (job_id,)
            )
            row = cursor.fetchone()
        
        if not row:
            return None
        
        return {
            'id': row['id'],
            'pipeline_name': row['pipeline_name'],
            'user_id': row['user_id'],
            'status': row['status'],
            'parameters': json.loads(row['parameters']),
            'results': json.loads(row['results']) if row['results'] else None,
            'error_message': row['error_message'],
            'created_at': row['created_at'],
            'started_at': row['started_at'],
            'completed_at': row['completed_at'],
            'execution_time': row['execution_time']
        }
    
    def update_job_status(self, job_id: str, status: str):
        """Update job status"""
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                'UPDATE jobs SET status = ? WHERE id = ?',
                (status, job_id)
            )
            conn.commit()
        
        logger.info(f"✅ Job {job_id} status updated to {status}")
    
    def update_job_results(self, job_id: str, results: dict):
        """Update job results"""
        
        now = datetime.utcnow().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                'UPDATE jobs SET results = ?, completed_at = ? WHERE id = ?',
                (json.dumps(results), now, job_id)
            )
            conn.commit()
    
    def update_job_error(self, job_id: str, error: str):
        """Update job error"""
        
        now = datetime.utcnow().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                'UPDATE jobs SET error_message = ?, completed_at = ? WHERE id = ?',
                (error, now, job_id)
            )
            conn.commit()
    
    def list_jobs(self, limit: int = 50):
        """List recent jobs"""
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                'SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?',
                (limit,)
            )
            rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
