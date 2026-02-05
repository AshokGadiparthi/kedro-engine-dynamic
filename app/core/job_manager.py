"""
Complete Database Manager - 100% WORKING
Creates ALL tables for the entire application
No broken functionality - backward compatible
"""

import sqlite3
from datetime import datetime
from pathlib import Path
import logging
import json
import uuid

logger = logging.getLogger(__name__)

DB_PATH = Path.cwd() / "ml_platform.db"


class DatabaseManager:
    """Manage all database operations"""
    
    def __init__(self):
        self.db_path = DB_PATH
        self._init_db()
    
    def _init_db(self):
        """Initialize database with ALL required tables"""
        try:
            # Ensure directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            with sqlite3.connect(str(self.db_path)) as conn:
                # Create USERS table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id TEXT PRIMARY KEY,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE,
                        password_hash TEXT NOT NULL,
                        full_name TEXT,
                        is_active BOOLEAN DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create PROJECTS table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS projects (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT,
                        owner_id TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (owner_id) REFERENCES users(id)
                    )
                ''')
                
                # Create DATASETS table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS datasets (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        project_id TEXT NOT NULL,
                        description TEXT,
                        file_path TEXT,
                        file_size INTEGER,
                        file_name TEXT,
                        rows INTEGER,
                        columns INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (project_id) REFERENCES projects(id)
                    )
                ''')
                
                # Create DATASOURCES table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS datasources (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        project_id TEXT NOT NULL,
                        source_type TEXT NOT NULL,
                        connection_string TEXT,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (project_id) REFERENCES projects(id)
                    )
                ''')
                
                # Create MODELS table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS models (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        project_id TEXT NOT NULL,
                        model_type TEXT NOT NULL,
                        description TEXT,
                        version TEXT,
                        parameters TEXT,
                        metrics TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (project_id) REFERENCES projects(id)
                    )
                ''')
                
                # Create ACTIVITIES table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS activities (
                        id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        action TEXT NOT NULL,
                        entity_type TEXT NOT NULL,
                        entity_id TEXT NOT NULL,
                        details TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                ''')
                
                # Create JOBS table (for Celery/pipeline jobs)
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
                
                # Create EDA_JOBS table (for tracking EDA analysis)
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS eda_jobs (
                        id TEXT PRIMARY KEY,
                        dataset_id TEXT NOT NULL,
                        status TEXT DEFAULT 'pending',
                        current_phase TEXT,
                        progress INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        started_at TIMESTAMP,
                        completed_at TIMESTAMP,
                        error_message TEXT,
                        FOREIGN KEY (dataset_id) REFERENCES datasets(id)
                    )
                ''')
                
                # Create EDA_RESULTS table (for storing EDA analysis results)
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS eda_results (
                        id TEXT PRIMARY KEY,
                        dataset_id TEXT NOT NULL,
                        eda_job_id TEXT NOT NULL,
                        phase INTEGER,
                        result_type TEXT,
                        result_data TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (dataset_id) REFERENCES datasets(id),
                        FOREIGN KEY (eda_job_id) REFERENCES eda_jobs(id)
                    )
                ''')
                
                # Create STATISTICS table (for dataset statistics)
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS statistics (
                        id TEXT PRIMARY KEY,
                        dataset_id TEXT NOT NULL,
                        column_name TEXT NOT NULL,
                        stat_type TEXT NOT NULL,
                        stat_value TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (dataset_id) REFERENCES datasets(id)
                    )
                ''')
                
                # Create CORRELATIONS table (for correlation analysis)
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS correlations (
                        id TEXT PRIMARY KEY,
                        dataset_id TEXT NOT NULL,
                        column1 TEXT NOT NULL,
                        column2 TEXT NOT NULL,
                        correlation_value REAL,
                        p_value REAL,
                        phase INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (dataset_id) REFERENCES datasets(id)
                    )
                ''')
                
                # Create QUALITY_METRICS table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS quality_metrics (
                        id TEXT PRIMARY KEY,
                        dataset_id TEXT NOT NULL,
                        metric_name TEXT NOT NULL,
                        metric_value REAL,
                        metric_data TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (dataset_id) REFERENCES datasets(id)
                    )
                ''')
                
                # Create OUTLIERS table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS outliers (
                        id TEXT PRIMARY KEY,
                        dataset_id TEXT NOT NULL,
                        column_name TEXT NOT NULL,
                        outlier_method TEXT,
                        outlier_count INTEGER,
                        outlier_indices TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (dataset_id) REFERENCES datasets(id)
                    )
                ''')
                
                # Create DISTRIBUTIONS table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS distributions (
                        id TEXT PRIMARY KEY,
                        dataset_id TEXT NOT NULL,
                        column_name TEXT NOT NULL,
                        distribution_type TEXT,
                        distribution_data TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (dataset_id) REFERENCES datasets(id)
                    )
                ''')
                
                # Create NORMALITY_TESTS table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS normality_tests (
                        id TEXT PRIMARY KEY,
                        dataset_id TEXT NOT NULL,
                        column_name TEXT NOT NULL,
                        test_type TEXT,
                        statistic REAL,
                        p_value REAL,
                        is_normal BOOLEAN,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (dataset_id) REFERENCES datasets(id)
                    )
                ''')
                
                # Create VIF_ANALYSIS table (Variance Inflation Factor)
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS vif_analysis (
                        id TEXT PRIMARY KEY,
                        dataset_id TEXT NOT NULL,
                        column_name TEXT NOT NULL,
                        vif_value REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (dataset_id) REFERENCES datasets(id)
                    )
                ''')
                
                # Create FEATURE_CLUSTERING table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS feature_clustering (
                        id TEXT PRIMARY KEY,
                        dataset_id TEXT NOT NULL,
                        cluster_data TEXT,
                        cluster_count INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (dataset_id) REFERENCES datasets(id)
                    )
                ''')
                
                # Create MULTICOLLINEARITY_WARNINGS table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS multicollinearity_warnings (
                        id TEXT PRIMARY KEY,
                        dataset_id TEXT NOT NULL,
                        column1 TEXT NOT NULL,
                        column2 TEXT NOT NULL,
                        correlation REAL,
                        warning_level TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (dataset_id) REFERENCES datasets(id)
                    )
                ''')
                
                # Create PIPELINES table (for pipeline configurations)
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS pipelines (
                        id TEXT PRIMARY KEY,
                        name TEXT UNIQUE NOT NULL,
                        description TEXT,
                        parameters TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create SESSION_CACHE table (for caching session data)
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS session_cache (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        expires_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
            
            logger.info(f"✅ Database initialized at: {self.db_path}")
            logger.info("✅ Created 20 tables successfully!")
        
        except Exception as e:
            logger.error(f"❌ Database initialization error: {e}")
            raise
    
    # Job operations (backward compatible)
    def create_job(self, pipeline_name: str, user_id: str = None, parameters: dict = None) -> dict:
        """Create a new job"""
        job_id = str(uuid.uuid4())
        
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute('''
                    INSERT INTO jobs (id, pipeline_name, user_id, parameters, status)
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
        except Exception as e:
            logger.error(f"❌ Error creating job: {e}")
            raise
    
    def get_job(self, job_id: str) -> dict:
        """Get job details"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('SELECT * FROM jobs WHERE id = ?', (job_id,))
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
        except Exception as e:
            logger.error(f"❌ Error getting job: {e}")
            raise
    
    def update_job_status(self, job_id: str, status: str):
        """Update job status"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute('UPDATE jobs SET status = ? WHERE id = ?', (status, job_id))
                conn.commit()
        except Exception as e:
            logger.error(f"❌ Error updating job: {e}")
            raise
    
    def update_job_results(self, job_id: str, results: dict):
        """Update job results"""
        now = datetime.utcnow().isoformat()
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute(
                    'UPDATE jobs SET results = ?, completed_at = ? WHERE id = ?',
                    (json.dumps(results), now, job_id)
                )
                conn.commit()
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            raise
    
    def update_job_error(self, job_id: str, error: str):
        """Update job error"""
        now = datetime.utcnow().isoformat()
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute(
                    'UPDATE jobs SET error_message = ?, completed_at = ? WHERE id = ?',
                    (error, now, job_id)
                )
                conn.commit()
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            raise
    
    def list_jobs(self, limit: int = 50):
        """List jobs"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    'SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?',
                    (limit,)
                )
                rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            raise


# Backward compatibility alias
JobManager = DatabaseManager
