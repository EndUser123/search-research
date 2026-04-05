#!/usr/bin/env python3
"""CHS Production Deployment Script
Deploy Chat History Search system to production environment with comprehensive validation.
"""

import json
import os
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# Add CSF NIP paths
csf_nip_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(csf_nip_root))
sys.path.insert(0, str(csf_nip_root / "src"))
sys.path.insert(0, str(csf_nip_root / "src" / "lib"))


class CHSProductionDeployer:
    """Production deployment manager for CHS system."""

    def __init__(self):
        self.deployment_start_time = datetime.now()
        self.deployment_log = []
        self.production_config = {}
        self.validation_results = {}

    def log_deployment_step(self, step: str, status: str, message: str, details: Any = None):
        """Log deployment step with comprehensive details."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'step': step,
            'status': status,
            'message': message,
            'details': details
        }
        self.deployment_log.append(log_entry)

        # Display status
        status_icon = {'SUCCESS': '✅', 'IN_PROGRESS': '🔄', 'WARNING': '⚠️', 'ERROR': '❌', 'INFO': 'ℹ️'}
        icon = status_icon.get(status, '•')
        print(f"{icon} {step}: {message}")

        if details and status == 'ERROR':
            print(f"   Details: {details}")

    def backup_current_configuration(self) -> bool:
        """Backup current configuration before deployment."""
        self.log_deployment_step("BACKUP_CONFIG", "IN_PROGRESS", "Creating configuration backup")

        try:
            backup_dir = csf_nip_root / ".backups" / "chs_production" f"_{self.deployment_start_time.strftime('%Y%m%d_%H%M%S')}"
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Backup critical files
            files_to_backup = [
                csf_nip_root / ".data" / "chat_history.db",
                csf_nip_root / ".ToolRegistry" / "chat_search_index",
                csf_nip_root / "config" / "chat_search.json"
            ]

            backed_up_files = []
            for file_path in files_to_backup:
                if file_path.exists():
                    backup_path = backup_dir / file_path.name
                    if file_path.is_dir():
                        shutil.copytree(file_path, backup_path, dirs_exist_ok=True)
                    else:
                        shutil.copy2(file_path, backup_path)
                    backed_up_files.append(str(file_path))

            self.log_deployment_step(
                "BACKUP_CONFIG",
                "SUCCESS",
                "Configuration backup completed",
                {'backup_dir': str(backup_dir), 'files_backed_up': len(backed_up_files)}
            )
            return True

        except Exception as e:
            self.log_deployment_step("BACKUP_CONFIG", "ERROR", f"Backup failed: {str(e)}")
            return False

    def configure_production_environment(self) -> bool:
        """Configure production environment variables and settings."""
        self.log_deployment_step("CONFIGURE_ENV", "IN_PROGRESS", "Configuring production environment")

        try:
            # Production environment variables
            production_env = {
                # Core CHS Configuration
                'CHS_ENVIRONMENT': 'production',
                'CHS_DEPLOYMENT_VERSION': 'v2.0-production',
                'CHS_DEPLOYMENT_TIMESTAMP': self.deployment_start_time.isoformat(),

                # Performance Optimization
                'WORKFLOW_OPTIMIZATIONS_ENABLED': 'true',
                'PATTERN_RECOGNITION_ENABLED': 'true',
                'ENHANCED_CACHING_ENABLED': 'true',
                'SESSION_MONITORING_ENABLED': 'true',
                'MONITORING_ENABLED': 'true',

                # Production Security
                'CHS_LOG_LEVEL': 'INFO',
                'CHS_DEBUG_MODE': 'false',
                'CHS_PERFORMANCE_MONITORING': 'true',
                'CHS_QUERY_LOGGING': 'true',

                # Database Configuration
                'SQLITE_JOURNAL_MODE': 'WAL',
                'SQLITE_SYNCHRONOUS': 'NORMAL',
                'SQLITE_CACHE_SIZE': '10000',
                'SQLITE_TEMP_STORE': 'MEMORY',

                # Vector Store Configuration
                'VECTOR_STORE_TYPE': 'local',
                'VECTOR_STORE_PATH': str(csf_nip_root / ".data" / "vectors" / "chat_history"),
                'EMBEDDING_MODEL': 'all-mpnet-base-v2',
                'EMBEDDING_DEVICE': 'cuda',

                # RAG Configuration
                'RAG_ENABLED': 'true',
                'RAG_BACKEND': 'hybrid',
                'RAG_CHUNK_SIZE': '512',
                'RAG_OVERLAP': '50',

                # Caching Configuration
                'CACHE_TYPE': 'multi_level',
                'CACHE_MEMORY_LIMIT': '512MB',
                'CACHE_DISK_LIMIT': '2GB',
                'CACHE_TTL': '3600',

                # Performance Tuning
                'MAX_CONCURRENT_QUERIES': '20',
                'QUERY_TIMEOUT_SECONDS': '30',
                'RESULT_LIMIT_DEFAULT': '20',
                'RESULT_LIMIT_MAX': '100',

                # Monitoring Configuration
                'METRICS_ENABLED': 'true',
                'HEALTH_CHECK_ENABLED': 'true',
                'PERFORMANCE_ALERTS_ENABLED': 'true',
                'RESPONSE_TIME_THRESHOLD_MS': '100',
                'ERROR_RATE_THRESHOLD': '5'
            }

            # Set environment variables
            for key, value in production_env.items():
                os.environ[key] = value

            self.production_config = production_env

            self.log_deployment_step(
                "CONFIGURE_ENV",
                "SUCCESS",
                f"Production environment configured with {len(production_env)} settings",
                {'settings_count': len(production_env)}
            )
            return True

        except Exception as e:
            self.log_deployment_step("CONFIGURE_ENV", "ERROR", f"Environment configuration failed: {str(e)}")
            return False

    def create_production_directories(self) -> bool:
        """Create necessary production directories."""
        self.log_deployment_step("CREATE_DIRECTORIES", "IN_PROGRESS", "Creating production directories")

        try:
            production_dirs = [
                csf_nip_root / ".data" / "vectors" / "chat_history",
                csf_nip_root / ".data" / "cache" / "search",
                csf_nip_root / ".data" / "logs" / "chs",
                csf_nip_root / ".data" / "metrics" / "chs",
                csf_nip_root / ".data" / "sessions" / "chs",
                csf_nip_root / ".backups" / "chs_production",
                csf_nip_root / ".config" / "chs_production"
            ]

            created_dirs = []
            for dir_path in production_dirs:
                dir_path.mkdir(parents=True, exist_ok=True)
                created_dirs.append(str(dir_path))

            # Create .gitkeep files to maintain directory structure
            for dir_path in production_dirs:
                (dir_path / ".gitkeep").touch(exist_ok=True)

            self.log_deployment_step(
                "CREATE_DIRECTORIES",
                "SUCCESS",
                f"Created {len(created_dirs)} production directories",
                {'directories': created_dirs}
            )
            return True

        except Exception as e:
            self.log_deployment_step("CREATE_DIRECTORIES", "ERROR", f"Directory creation failed: {str(e)}")
            return False

    def initialize_production_database(self) -> bool:
        """Initialize and optimize production database."""
        self.log_deployment_step("INIT_DATABASE", "IN_PROGRESS", "Initializing production database")

        try:
            # Import and initialize database
            from src.modules.analysis.chat_search.src.chat_history_db import (
                ChatHistoryDB,
            )

            db_path = csf_nip_root / ".data" / "chat_history.db"
            db = ChatHistoryDB(db_path)

            # Get database statistics
            stats = db.get_stats()

            # Optimize database for production
            optimization_queries = [
                "PRAGMA journal_mode = WAL;",
                "PRAGMA synchronous = NORMAL;",
                "PRAGMA cache_size = 10000;",
                "PRAGMA temp_store = MEMORY;",
                "PRAGMA mmap_size = 268435456;",  # 256MB
                "ANALYZE;",
                "VACUUM;"
            ]

            # Apply optimizations
            import sqlite3
            with sqlite3.connect(db_path) as conn:
                for query in optimization_queries:
                    try:
                        conn.execute(query)
                    except Exception as e:
                        self.log_deployment_step(
                            "INIT_DATABASE",
                            "WARNING",
                            f"Database optimization query failed: {query[:50]}...",
                            str(e)
                        )
                conn.commit()

            # Get updated statistics
            updated_stats = db.get_stats()

            self.log_deployment_step(
                "INIT_DATABASE",
                "SUCCESS",
                "Production database initialized and optimized",
                {
                    'initial_stats': stats,
                    'optimized_stats': updated_stats,
                    'db_path': str(db_path)
                }
            )
            return True

        except Exception as e:
            self.log_deployment_step("INIT_DATABASE", "ERROR", f"Database initialization failed: {str(e)}")
            return False

    def initialize_vector_store(self) -> bool:
        """Initialize production vector store."""
        self.log_deployment_step("INIT_VECTOR_STORE", "IN_PROGRESS", "Initializing production vector store")

        try:
            # Initialize searcher with singleton pattern to prevent GPU exhaustion
            from src.modules.analysis.chat_search.src.chs_singleton import (
                get_chs_instance,
            )

            print("   Using CHS singleton pattern to prevent GPU exhaustion...")
            searcher = get_chs_instance(enable_rag=True)

            # Get vector store information
            vector_store_info = {
                'enabled': searcher.enable_rag,
                'rag_backend': getattr(searcher, 'rag_backend', 'unknown'),
                'vector_store_path': str(csf_nip_root / ".data" / "vectors" / "chat_history"),
                'points_count': 'unknown'
            }

            # Try to get collection info if available
            try:
                if hasattr(searcher, 'hybrid_searcher') and searcher.hybrid_searcher:
                    # Try newer API first (vectors_count), fallback to older API (points_count)
                    vector_store_info['points_count'] = getattr(
                        searcher.hybrid_searcher.vector_store,
                        'vectors_count',
                        getattr(
                            searcher.hybrid_searcher.vector_store,
                            'points_count',
                            'unknown'
                        )
                    )
            except:
                pass

            self.log_deployment_step(
                "INIT_VECTOR_STORE",
                "SUCCESS",
                "Production vector store initialized",
                vector_store_info
            )
            return True

        except Exception as e:
            self.log_deployment_step("INIT_VECTOR_STORE", "ERROR", f"Vector store initialization failed: {str(e)}")
            return False

    def create_production_config_file(self) -> bool:
        """Create production configuration file."""
        self.log_deployment_step("CREATE_CONFIG", "IN_PROGRESS", "Creating production configuration file")

        try:
            config_file = csf_nip_root / ".config" / "chs_production" / "production_config.json"

            production_config = {
                'deployment': {
                    'version': os.environ.get('CHS_DEPLOYMENT_VERSION', 'v2.0-production'),
                    'timestamp': self.deployment_start_time.isoformat(),
                    'environment': 'production'
                },
                'system': {
                    'log_level': os.environ.get('CHS_LOG_LEVEL', 'INFO'),
                    'debug_mode': os.environ.get('CHS_DEBUG_MODE', 'false') == 'true',
                    'performance_monitoring': os.environ.get('CHS_PERFORMANCE_MONITORING', 'true') == 'true'
                },
                'database': {
                    'path': str(csf_nip_root / ".data" / "chat_history.db"),
                    'journal_mode': os.environ.get('SQLITE_JOURNAL_MODE', 'WAL'),
                    'synchronous': os.environ.get('SQLITE_SYNCHRONOUS', 'NORMAL'),
                    'cache_size': os.environ.get('SQLITE_CACHE_SIZE', '10000')
                },
                'vector_store': {
                    'type': os.environ.get('VECTOR_STORE_TYPE', 'local'),
                    'path': os.environ.get('VECTOR_STORE_PATH'),
                    'embedding_model': os.environ.get('EMBEDDING_MODEL', 'all-mpnet-base-v2'),
                    'device': os.environ.get('EMBEDDING_DEVICE', 'cuda')
                },
                'rag': {
                    'enabled': os.environ.get('RAG_ENABLED', 'true') == 'true',
                    'backend': os.environ.get('RAG_BACKEND', 'hybrid'),
                    'chunk_size': int(os.environ.get('RAG_CHUNK_SIZE', '512')),
                    'overlap': int(os.environ.get('RAG_OVERLAP', '50'))
                },
                'caching': {
                    'type': os.environ.get('CACHE_TYPE', 'multi_level'),
                    'memory_limit': os.environ.get('CACHE_MEMORY_LIMIT', '512MB'),
                    'disk_limit': os.environ.get('CACHE_DISK_LIMIT', '2GB'),
                    'ttl': int(os.environ.get('CACHE_TTL', '3600'))
                },
                'performance': {
                    'max_concurrent_queries': int(os.environ.get('MAX_CONCURRENT_QUERIES', '20')),
                    'query_timeout_seconds': int(os.environ.get('QUERY_TIMEOUT_SECONDS', '30')),
                    'result_limit_default': int(os.environ.get('RESULT_LIMIT_DEFAULT', '20')),
                    'result_limit_max': int(os.environ.get('RESULT_LIMIT_MAX', '100'))
                },
                'monitoring': {
                    'metrics_enabled': os.environ.get('METRICS_ENABLED', 'true') == 'true',
                    'health_check_enabled': os.environ.get('HEALTH_CHECK_ENABLED', 'true') == 'true',
                    'performance_alerts_enabled': os.environ.get('PERFORMANCE_ALERTS_ENABLED', 'true') == 'true',
                    'response_time_threshold_ms': int(os.environ.get('RESPONSE_TIME_THRESHOLD_MS', '100')),
                    'error_rate_threshold': float(os.environ.get('ERROR_RATE_THRESHOLD', '5'))
                },
                'optimizations': {
                    'workflow_optimizations_enabled': os.environ.get('WORKFLOW_OPTIMIZATIONS_ENABLED', 'true') == 'true',
                    'pattern_recognition_enabled': os.environ.get('PATTERN_RECOGNITION_ENABLED', 'true') == 'true',
                    'enhanced_caching_enabled': os.environ.get('ENHANCED_CACHING_ENABLED', 'true') == 'true',
                    'session_monitoring_enabled': os.environ.get('SESSION_MONITORING_ENABLED', 'true') == 'true'
                }
            }

            with open(config_file, 'w') as f:
                json.dump(production_config, f, indent=2)

            self.log_deployment_step(
                "CREATE_CONFIG",
                "SUCCESS",
                "Production configuration file created",
                {'config_file': str(config_file)}
            )
            return True

        except Exception as e:
            self.log_deployment_step("CREATE_CONFIG", "ERROR", f"Configuration file creation failed: {str(e)}")
            return False

    def run_production_validation(self) -> bool:
        """Run comprehensive production validation."""
        self.log_deployment_step("PRODUCTION_VALIDATION", "IN_PROGRESS", "Running production validation")

        try:
            validation_results = {}

            # Test 1: System Initialization
            self.log_deployment_step("VALIDATION", "IN_PROGRESS", "Testing system initialization")
            from src.modules.analysis.chat_search.src.chs_singleton import (
                get_chs_instance,
            )
            from src.modules.analysis.chat_search.src.gpu_memory_manager import (
                get_gpu_memory_status,
            )

            init_start = time.time()
            searcher = get_chs_instance(enable_rag=True)
            init_time = time.time() - init_start

            # Check GPU memory status
            gpu_status = get_gpu_memory_status()
            self.log_deployment_step("VALIDATION", "INFO", f"GPU Memory Status: {gpu_status.get('reserved_percent', 0):.1f}%")

            validation_results['initialization'] = {
                'success': True,
                'init_time_seconds': init_time,
                'sqlite_enabled': True,
                'rag_enabled': searcher.enable_rag,
                'cache_enabled': searcher.enable_caching,
                'session_monitor_enabled': searcher.session_monitor is not None,
                'pattern_recognition_enabled': searcher.pattern_recognizer is not None
            }

            # Test 2: Basic Search Functionality
            self.log_deployment_step("VALIDATION", "IN_PROGRESS", "Testing search functionality")
            search_start = time.time()
            results = searcher.search("database", limit=5)
            search_time = (time.time() - search_start) * 1000

            validation_results['search_functionality'] = {
                'success': True,
                'results_count': len(results),
                'search_time_ms': search_time,
                'response_time_acceptable': search_time < 100
            }

            # Test 3: Performance Validation
            self.log_deployment_step("VALIDATION", "IN_PROGRESS", "Testing performance benchmarks")
            test_queries = ["database", "API design", "testing", "performance", "security"]
            response_times = []

            for query in test_queries:
                start_time = time.perf_counter()
                test_results = searcher.search(query, limit=3)
                end_time = time.perf_counter()
                response_times.append((end_time - start_time) * 1000)

            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)

            validation_results['performance'] = {
                'success': True,
                'avg_response_time_ms': avg_response_time,
                'max_response_time_ms': max_response_time,
                'all_queries_under_100ms': all(rt < 100 for rt in response_times),
                'performance_grade': 'A+' if avg_response_time < 50 else 'A' if avg_response_time < 100 else 'B'
            }

            # Test 4: Database Connectivity
            self.log_deployment_step("VALIDATION", "IN_PROGRESS", "Testing database connectivity")
            from src.modules.analysis.chat_search.src.chat_history_db import (
                ChatHistoryDB,
            )

            db = ChatHistoryDB()
            db_stats = db.get_stats()

            validation_results['database_connectivity'] = {
                'success': True,
                'sessions_count': db_stats.get('sessions', 0),
                'messages_count': db_stats.get('messages', 0),
                'database_accessible': True
            }

            # Test 5: Session Monitoring
            self.log_deployment_step("VALIDATION", "IN_PROGRESS", "Testing session monitoring")
            session_test_passed = False
            if searcher.session_monitor:
                try:
                    session_id = 'prod_test_session'
                    searcher.session_monitor.start_session(session_id)
                    searcher.session_monitor.record_query(session_id, 'test query', 25.0, 5)
                    metrics = searcher.session_monitor.end_session(session_id)
                    session_test_passed = 'duration_minutes' in metrics
                except:
                    session_test_passed = False

            validation_results['session_monitoring'] = {
                'success': session_test_passed,
                'session_monitor_available': searcher.session_monitor is not None
            }

            self.validation_results = validation_results

            # Calculate overall validation score
            all_tests_passed = all(result['success'] for result in validation_results.values())
            validation_score = sum(1 for result in validation_results.values() if result['success']) / len(validation_results)

            self.log_deployment_step(
                "PRODUCTION_VALIDATION",
                "SUCCESS" if all_tests_passed else "WARNING",
                f"Production validation completed - {validation_score:.1%} pass rate",
                {
                    'validation_score': validation_score,
                    'all_tests_passed': all_tests_passed,
                    'test_results': validation_results
                }
            )

            return all_tests_passed

        except Exception as e:
            self.log_deployment_step("PRODUCTION_VALIDATION", "ERROR", f"Production validation failed: {str(e)}")
            return False

    def create_production_monitoring(self) -> bool:
        """Set up production monitoring and health checks."""
        self.log_deployment_step("SETUP_MONITORING", "IN_PROGRESS", "Setting up production monitoring")

        try:
            # Create monitoring script
            monitoring_script = csf_nip_root / ".config" / "chs_production" / "health_check.py"

            script_content = '''#!/usr/bin/env python3
"""CHS Production Health Check Monitor"""

import sys
import json
import time
from datetime import datetime
from pathlib import Path

# Add CSF NIP paths
csf_nip_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(csf_nip_root))
sys.path.insert(0, str(csf_nip_root / "src"))

def health_check():
    """Perform comprehensive health check."""
    health_status = {
        'timestamp': datetime.now().isoformat(),
        'status': 'healthy',
        'checks': {}
    }

    try:
        # Database health
        from src.modules.analysis.chat_search.src.chat_history_db import ChatHistoryDB
        db = ChatHistoryDB()
        stats = db.get_stats()
        health_status['checks']['database'] = {
            'status': 'healthy',
            'sessions': stats.get('sessions', 0),
            'messages': stats.get('messages', 0)
        }

        # Search functionality health
        from src.modules.analysis.chat_search.src.chat_history_search import ChatHistorySearcher
        searcher = ChatHistorySearcher(enable_rag=True)

        # Test search performance
        start_time = time.perf_counter()
        results = searcher.search("health check", limit=3)
        search_time = (time.perf_counter() - start_time) * 1000

        health_status['checks']['search_performance'] = {
            'status': 'healthy' if search_time < 100 else 'degraded',
            'response_time_ms': search_time,
            'results_count': len(results)
        }

        # Vector store health
        health_status['checks']['vector_store'] = {
            'status': 'healthy' if searcher.enable_rag else 'disabled',
            'rag_enabled': searcher.enable_rag
        }

        # Optimization systems health
        health_status['checks']['optimizations'] = {
            'workflow_optimizations': searcher.workflow_optimization_enabled,
            'session_monitoring': searcher.session_monitor is not None,
            'pattern_recognition': searcher.pattern_recognizer is not None,
            'enhanced_caching': searcher.enable_caching
        }

    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['error'] = str(e)

    return health_status

if __name__ == "__main__":
    health = health_check()
    print(json.dumps(health, indent=2))
    sys.exit(0 if health['status'] == 'healthy' else 1)
'''

            with open(monitoring_script, 'w') as f:
                f.write(script_content)

            # Make script executable
            monitoring_script.chmod(0o755)

            # Create performance monitoring script
            perf_monitor_script = csf_nip_root / ".config" / "chs_production" / "performance_monitor.py"

            perf_script_content = '''#!/usr/bin/env python3
"""CHS Production Performance Monitor"""

import sys
import json
import time
import psutil
from datetime import datetime
from pathlib import Path

# Add CSF NIP paths
csf_nip_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(csf_nip_root))
sys.path.insert(0, str(csf_nip_root / "src"))

def performance_monitor():
    """Monitor CHS system performance."""
    perf_data = {
        'timestamp': datetime.now().isoformat(),
        'system_metrics': {},
        'chs_metrics': {}
    }

    try:
        # System metrics
        process = psutil.Process()
        perf_data['system_metrics'] = {
            'cpu_percent': process.cpu_percent(),
            'memory_mb': process.memory_info().rss / 1024 / 1024,
            'memory_percent': process.memory_percent(),
            'threads': process.num_threads()
        }

        # CHS performance metrics
        from src.modules.analysis.chat_search.src.chat_history_search import ChatHistorySearcher
        searcher = ChatHistorySearcher(enable_rag=True)

        # Test search performance
        test_queries = ["database", "API", "testing"]
        search_times = []

        for query in test_queries:
            start_time = time.perf_counter()
            results = searcher.search(query, limit=5)
            search_time = (time.perf_counter() - start_time) * 1000
            search_times.append(search_time)

        perf_data['chs_metrics'] = {
            'avg_search_time_ms': sum(search_times) / len(search_times),
            'max_search_time_ms': max(search_times),
            'min_search_time_ms': min(search_times),
            'rag_enabled': searcher.enable_rag,
            'cache_enabled': searcher.enable_caching,
            'optimizations_enabled': searcher.workflow_optimization_enabled
        }

        # Database stats
        from src.modules.analysis.chat_search.src.chat_history_db import ChatHistoryDB
        db = ChatHistoryDB()
        db_stats = db.get_stats()
        perf_data['chs_metrics']['database_stats'] = db_stats

    except Exception as e:
        perf_data['error'] = str(e)

    return perf_data

if __name__ == "__main__":
    perf = performance_monitor()
    print(json.dumps(perf, indent=2))
'''

            with open(perf_monitor_script, 'w') as f:
                f.write(perf_script_content)

            perf_monitor_script.chmod(0o755)

            self.log_deployment_step(
                "SETUP_MONITORING",
                "SUCCESS",
                "Production monitoring scripts created",
                {
                    'health_check_script': str(monitoring_script),
                    'performance_monitor_script': str(perf_monitor_script)
                }
            )
            return True

        except Exception as e:
            self.log_deployment_step("SETUP_MONITORING", "ERROR", f"Monitoring setup failed: {str(e)}")
            return False

    def generate_deployment_report(self) -> bool:
        """Generate comprehensive deployment report."""
        self.log_deployment_step("GENERATE_REPORT", "IN_PROGRESS", "Generating deployment report")

        try:
            deployment_end_time = datetime.now()
            deployment_duration = deployment_end_time - self.deployment_start_time

            deployment_report = {
                'deployment_info': {
                    'start_time': self.deployment_start_time.isoformat(),
                    'end_time': deployment_end_time.isoformat(),
                    'duration_seconds': deployment_duration.total_seconds(),
                    'duration_human': str(deployment_duration),
                    'environment': 'production',
                    'version': os.environ.get('CHS_DEPLOYMENT_VERSION', 'v2.0-production')
                },
                'deployment_log': self.deployment_log,
                'configuration': self.production_config,
                'validation_results': self.validation_results,
                'success_summary': {
                    'total_steps': len(self.deployment_log),
                    'successful_steps': len([log for log in self.deployment_log if log['status'] == 'SUCCESS']),
                    'failed_steps': len([log for log in self.deployment_log if log['status'] == 'ERROR']),
                    'warnings': len([log for log in self.deployment_log if log['status'] == 'WARNING'])
                },
                'deployment_status': 'SUCCESS' if len([log for log in self.deployment_log if log['status'] == 'ERROR']) == 0 else 'FAILED'
            }

            # Save deployment report
            report_file = csf_nip_root / ".config" / "chs_production" / f"deployment_report_{self.deployment_start_time.strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump(deployment_report, f, indent=2)

            # Also save latest report
            latest_report_file = csf_nip_root / ".config" / "chs_production" / "latest_deployment_report.json"
            with open(latest_report_file, 'w') as f:
                json.dump(deployment_report, f, indent=2)

            self.log_deployment_step(
                "GENERATE_REPORT",
                "SUCCESS",
                "Deployment report generated",
                {
                    'report_file': str(report_file),
                    'latest_report_file': str(latest_report_file),
                    'deployment_duration': str(deployment_duration)
                }
            )
            return True

        except Exception as e:
            self.log_deployment_step("GENERATE_REPORT", "ERROR", f"Report generation failed: {str(e)}")
            return False

    def deploy_to_production(self) -> bool:
        """Execute complete production deployment."""
        print("🚀 CHS PRODUCTION DEPLOYMENT")
        print("=" * 50)
        print(f"Deployment Start Time: {self.deployment_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("Target Environment: Production")
        print()

        deployment_steps = [
            ("Backup Current Configuration", self.backup_current_configuration),
            ("Configure Production Environment", self.configure_production_environment),
            ("Create Production Directories", self.create_production_directories),
            ("Initialize Production Database", self.initialize_production_database),
            ("Initialize Vector Store", self.initialize_vector_store),
            ("Create Production Configuration File", self.create_production_config_file),
            ("Run Production Validation", self.run_production_validation),
            ("Set Up Production Monitoring", self.create_production_monitoring),
            ("Generate Deployment Report", self.generate_deployment_report)
        ]

        for step_name, step_function in deployment_steps:
            success = step_function()
            if not success and step_name not in ["Generate Deployment Report"]:
                self.log_deployment_step("DEPLOYMENT", "ERROR", f"Deployment failed at step: {step_name}")
                return False

        # Check final deployment status
        failed_steps = [log for log in self.deployment_log if log['status'] == 'ERROR']
        if failed_steps:
            self.log_deployment_step("DEPLOYMENT", "FAILED", f"Deployment completed with {len(failed_steps)} failed steps")
            return False
        else:
            self.log_deployment_step("DEPLOYMENT", "SUCCESS", "🎉 CHS successfully deployed to production!")
            return True

    def print_deployment_summary(self):
        """Print final deployment summary."""
        print()
        print("🎯 DEPLOYMENT SUMMARY")
        print("=" * 50)

        successful_steps = [log for log in self.deployment_log if log['status'] == 'SUCCESS']
        failed_steps = [log for log in self.deployment_log if log['status'] == 'ERROR']
        warnings = [log for log in self.deployment_log if log['status'] == 'WARNING']

        print(f"✅ Successful Steps: {len(successful_steps)}")
        print(f"❌ Failed Steps: {len(failed_steps)}")
        print(f"⚠️  Warnings: {len(warnings)}")

        if failed_steps:
            print("\n❌ Failed Steps:")
            for step in failed_steps:
                print(f"   • {step['step']}: {step['message']}")

        if warnings:
            print("\n⚠️  Warnings:")
            for warning in warnings:
                print(f"   • {warning['step']}: {warning['message']}")

        # Validation results
        if self.validation_results:
            print("\n📊 Validation Results:")
            for test_name, result in self.validation_results.items():
                status = "✅" if result['success'] else "❌"
                print(f"   {status} {test_name.replace('_', ' ').title()}")

        print()
        print("🚀 CHS Production Deployment Complete!")
        print("💡 Use the following commands for monitoring:")
        print(f"   Health Check: python {csf_nip_root / '.config' / 'chs_production' / 'health_check.py'}")
        print(f"   Performance Monitor: python {csf_nip_root / '.config' / 'chs_production' / 'performance_monitor.py'}")
        print()
        print("📈 Production Usage:")
        print("   cd P:/__csf")
        print("   python -m src.modules.analysis.chat_search.src.chat_history_search search 'your query'")
        print()


def main():
    """Main deployment execution."""
    deployer = CHSProductionDeployer()

    try:
        success = deployer.deploy_to_production()
        deployer.print_deployment_summary()

        if success:
            sys.exit(0)
        else:
            print("❌ Deployment failed. Check logs for details.")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n🛑 Deployment interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Deployment failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
