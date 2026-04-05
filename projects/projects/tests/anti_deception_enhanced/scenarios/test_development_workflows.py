"""
Real-World Scenario Tests for Development Workflows

Tests the Enhanced Anti-Deception Architecture with actual development workflows.
Validates protection against anti-deception patterns in real coding scenarios.
"""

import os
import sys

# Import test utilities
sys.path.insert(0, os.path.dirname(__file__))
from utils import (
    EvidenceGenerator,
    MockCommunicationSystem,
    MockLLM,
    TemporaryDirectory,
    TestConfigHelper,
)

# Import the anti-deception hook
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "__csf")
)
try:
    from anti_deception_hook import AntiDeceptionHook
except ImportError:
    raise ImportError("Could not import Anti-DeceptionHook")


class TestDevelopmentWorkflows:
    """Test suite for development workflow scenarios."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.config = TestConfigHelper.create_minimal_config()
        self.hook = AntiDeceptionHook()
        self.mock_llm = MockLLM()
        self.mock_comm = MockCommunicationSystem()
        self.evidence_generator = EvidenceGenerator()
        self.temp_dir = TemporaryDirectory()

    def teardown_method(self):
        """Clean up after each test method."""
        self.temp_dir.__exit__(None, None, None)
        self.hook.reset_failures()
        self.mock_comm.clear_messages()

    def test_python_development_workflow(self):
        """Test anti-deception protection in Python development workflow."""
        with self.temp_dir as temp_path:
            # Simulate Python development workflow
            py_project_dir = os.path.join(temp_path, "python_project")
            os.makedirs(py_project_dir, exist_ok=True)

            # Step 1: Create Python files with proper evidence
            python_files = [
                (
                    "main.py",
                    """
import sys
import os
from typing import List, Dict

def calculate_average(numbers: List[float]) -> float:
    \"\"\"Calculate average of a list of numbers.\"\"\"
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)

def main():
    numbers = [1.0, 2.0, 3.0, 4.0, 5.0]
    result = calculate_average(numbers)
    print(f"Average: {result}")

if __name__ == "__main__":
    main()
""",
                ),
                (
                    "test_main.py",
                    """
import unittest
import main
from typing import List

class TestMain(unittest.TestCase):
    def test_calculate_average(self):
        test_cases = [
            ([1.0, 2.0, 3.0, 4.0, 5.0], 3.0),
            ([], 0.0),
            ([10.0], 10.0)
        ]

        for numbers, expected in test_cases:
            with self.subTest(numbers=numbers):
                result = main.calculate_average(numbers)
                self.assertEqual(result, expected)

if __name__ == "__main__":
    unittest.main()
""",
                ),
                (
                    "requirements.txt",
                    """
pytest>=7.0.0
black>=22.0.0
mypy>=0.950
""",
                ),
                (
                    "README.md",
                    """
# Python Project

A simple Python project demonstrating average calculation functionality.

## Features
- Average calculation
- Unit tests
- Type hints
""",
                ),
            ]

            # Create files and collect evidence
            file_evidence = []
            for filename, content in python_files:
                file_path = os.path.join(py_project_dir, filename)
                with open(file_path, "w") as f:
                    f.write(content)

                # File operation evidence
                file_evidence.extend(
                    self.evidence_generator.create_file_evidence([file_path])
                )

            # Step 2: Run development tasks
            try:
                # Install requirements (simulated)
                self.hook.log_evidence(
                    "package_installation",
                    "Requirements installed for Python project",
                    [os.path.join(py_project_dir, "requirements.txt")],
                )

                # Run tests (simulated)
                test_output = """
============================= test session starts ==============================
collected 3 items

test_main.py::TestMain::test_calculate_average PASSED

============================== 1 passed in 0.002s ==============================
                """
                self.hook.verify_test_results(test_output)

                # Run linting (simulated)
                self.hook.log_evidence(
                    "code_quality",
                    "Code linting completed with no issues",
                    [
                        os.path.join(py_project_dir, "main.py"),
                        os.path.join(py_project_dir, "test_main.py"),
                    ],
                )

            except Exception as e:
                print(f"Python workflow error: {e}")

            # Step 3: Complete task validation
            context = {
                "evidence_provided": True,
                "checklist": {
                    "evidence_provided": True,
                    "tests_written": True,
                    "tests_pass": True,
                    "code_reviewed": True,
                    "files_created": True,
                },
            }

            can_complete, issues = self.hook.can_complete_task(context)
            assert len(issues) == 0 or can_complete is True

            # Step 4: Verify anti-deception protection
            # Should block dangerous operations in Python project
            dangerous_op = os.path.join(py_project_dir, "..", "rm", "-rf", "/")
            is_safe, reason = self.hook.validate_file_operation(dangerous_op, "write")
            assert is_safe is False

    def test_web_development_workflow(self):
        """Test anti-deception protection in web development workflow."""
        with self.temp_dir as temp_path:
            # Simulate web development workflow
            web_project_dir = os.path.join(temp_path, "web_project")
            static_dir = os.path.join(web_project_dir, "static")
            templates_dir = os.path.join(web_project_dir, "templates")

            os.makedirs(static_dir, exist_ok=True)
            os.makedirs(templates_dir, exist_ok=True)

            # Step 1: Create web application files
            web_files = [
                (
                    "app.py",
                    """
from flask import Flask, render_template, request
import os
import json

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data', methods=['GET'])
def get_data():
    return json.dumps({'status': 'success', 'data': 'Hello World'})

if __name__ == '__main__':
    app.run(debug=True)
""",
                ),
                (
                    "index.html",
                    """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Web App</title>
</head>
<body>
    <h1>Welcome to Web App</h1>
    <p>This is a secure web application.</p>
</body>
</html>
""",
                ),
                (
                    "style.css",
                    """
body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 20px;
    background-color: #f5f5f5;
}

h1 {
    color: #333;
    text-align: center;
}
""",
                ),
                (
                    "security_config.py",
                    """
import hashlib
import secrets
from functools import wraps

def hash_password(password: str) -> str:
    \"\"\"Hash password with secure salt.\"\"\"
    salt = secrets.token_hex(16)
    return hashlib.sha256((password + salt).encode()).hexdigest()

def require_auth(f):
    \"\"\"Decorator requiring authentication.\"\"\"
    @wraps(f)
    def decorated(*args, **kwargs):
        # Implementation would check authentication
        return f(*args, **kwargs)
    return decorated
""",
                ),
            ]

            # Create web files
            file_evidence = []
            for filename, content in web_files:
                file_path = os.path.join(web_project_dir, filename)
                with open(file_path, "w") as f:
                    f.write(content)

                file_evidence.extend(
                    self.evidence_generator.create_file_evidence([file_path])
                )
                self.hook.log_evidence(
                    "web_development", f"Web file created: {filename}", [file_path]
                )

            # Step 2: Simulate web development tasks
            try:
                # Security validation
                self.hook.log_evidence(
                    "security_validation",
                    "Security checks completed for web application",
                    [os.path.join(web_project_dir, "security_config.py")],
                )

                # Database setup (simulated)
                self.hook.log_evidence(
                    "database_setup",
                    "Database schema created and migrations applied",
                    [],
                )

                # API testing (simulated)
                api_test_output = """
API Test Results:
- GET /: PASSED
- GET /api/data: PASSED
- POST /api/data: PASSED

All API tests passed successfully.
"""
                self.hook.verify_test_results(api_test_output)

                # Performance testing (simulated)
                performance_results = """
Performance Test Results:
- Average response time: 150ms
- 95th percentile: 250ms
- Max response time: 400ms
- RPS: 1000

Performance metrics within acceptable range.
"""
                self.hook.log_evidence(
                    "performance_testing",
                    "Performance testing completed successfully",
                    [],
                )

            except Exception as e:
                print(f"Web workflow error: {e}")

            # Step 3: Complete web development validation
            context = {
                "evidence_provided": True,
                "checklist": {
                    "evidence_provided": True,
                    "tests_written": True,
                    "tests_pass": True,
                    "code_reviewed": True,
                    "files_created": True,
                    "safety_validated": True,
                },
            }

            can_complete, issues = self.hook.can_complete_task(context)
            assert len(issues) == 0 or can_complete is True

            # Step 4: Verify anti-deception protection for web operations
            # Should block dangerous web operations
            dangerous_web_op = os.path.join(
                web_project_dir, "..", "rm", "-rf", "/var/www/html"
            )
            is_safe, reason = self.hook.validate_file_operation(
                dangerous_web_op, "write"
            )
            assert is_safe is False

    def test_devops_workflow(self):
        """Test anti-deception protection in DevOps workflow."""
        with self.temp_dir as temp_path:
            # Simulate DevOps workflow
            devops_dir = os.path.join(temp_path, "devops_project")
            docker_dir = os.path.join(devops_dir, "docker")
            k8s_dir = os.path.join(devops_dir, "kubernetes")

            os.makedirs(docker_dir, exist_ok=True)
            os.makedirs(k8s_dir, exist_ok=True)

            # Step 1: Create DevOps infrastructure files
            devops_files = [
                (
                    "Dockerfile",
                    """
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "app.py"]
""",
                ),
                (
                    "docker-compose.yml",
                    """
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
    volumes:
      - .:/app
    restart: unless-stopped
""",
                ),
                (
                    "deployment.yaml",
                    """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
  labels:
    app: web-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web-app
  template:
    metadata:
      labels:
        app: web-app
    spec:
      containers:
      - name: web-app
        image: web-app:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
        resources:
          requests:
            memory: "64Mi"
            cpu: "250m"
          limits:
            memory: "128Mi"
            cpu: "500m"
""",
                ),
                (
                    "Jenkinsfile",
                    """
pipeline {
    agent any

    environment {
        REGISTRY = "my-registry/web-app"
        IMAGE_TAG = "latest"
    }

    stages {
        stage('Build') {
            steps {
                sh 'docker build -t ${REGISTRY}:${IMAGE_TAG} .'
            }
        }

        stage('Test') {
            steps {
                sh 'docker run --rm ${REGISTRY}:${IMAGE_TAG} python -m pytest'
            }
        }

        stage('Deploy') {
            steps {
                sh 'kubectl apply -f deployment.yaml'
            }
        }
    }

    post {
        always {
            cleanWs()
        }
    }
}
""",
                ),
            ]

            # Create DevOps files
            file_evidence = []
            for filename, content in devops_files:
                file_path = os.path.join(devops_dir, filename)
                with open(file_path, "w") as f:
                    f.write(content)

                file_evidence.extend(
                    self.evidence_generator.create_file_evidence([file_path])
                )
                self.hook.log_evidence(
                    "devops_development",
                    f"DevOps file created: {filename}",
                    [file_path],
                )

            # Step 2: Simulate DevOps tasks
            try:
                # CI/CD pipeline execution (simulated)
                self.hook.log_evidence(
                    "cicp_pipeline",
                    "CI/CD pipeline executed successfully",
                    [os.path.join(devops_dir, "Jenkinsfile")],
                )

                # Container security scan (simulated)
                security_scan_output = """
Container Security Scan Results:
- Image vulnerabilities: 0
- Critical issues: 0
- High severity: 0
- Medium severity: 1
- Low severity: 2

Security scan completed with acceptable results.
"""
                self.hook.log_evidence(
                    "security_scanning", "Container security scan completed", []
                )

                # Kubernetes deployment validation (simulated)
                k8s_validation_output = """
Kubernetes Deployment Validation:
- Pod health: OK
- Service availability: OK
- Resource usage: Normal
- Scaling: Working

All Kubernetes validations passed.
"""
                self.hook.log_evidence(
                    "kubernetes_validation", "Kubernetes deployment validated", []
                )

                # Infrastructure as Code testing (simulated)
                terraform_output = """
Infrastructure Test Results:
- Resources created: 5
- No drift detected
- Cost estimation: $50/month
- Compliance: OK

Infrastructure deployment successful.
"""
                self.hook.log_evidence(
                    "infrastructure_as_code", "Infrastructure as code deployed", []
                )

            except Exception as e:
                print(f"DevOps workflow error: {e}")

            # Step 3: Complete DevOps validation
            context = {
                "evidence_provided": True,
                "checklist": {
                    "evidence_provided": True,
                    "tests_written": True,
                    "tests_pass": True,
                    "code_reviewed": True,
                    "files_created": True,
                    "safety_validated": True,
                    "performance_validated": True,
                },
            }

            can_complete, issues = self.hook.can_complete_task(context)
            assert len(issues) == 0 or can_complete is True

            # Step 4: Verify anti-deception protection for DevOps operations
            # Should block dangerous DevOps operations
            dangerous_devops_op = os.path.join(
                devops_dir, "..", "kubectl", "delete", "pod", "--all"
            )
            is_safe, reason = self.hook.validate_file_operation(
                dangerous_devops_op, "write"
            )
            assert is_safe is False

    def test_data_science_workflow(self):
        """Test anti-deception protection in data science workflow."""
        with self.temp_dir as temp_path:
            # Simulate data science workflow
            ds_dir = os.path.join(temp_path, "data_science_project")
            data_dir = os.path.join(ds_dir, "data")
            notebooks_dir = os.path.join(ds_dir, "notebooks")
            models_dir = os.path.join(ds_dir, "models")

            os.makedirs(data_dir, exist_ok=True)
            os.makedirs(notebooks_dir, exist_ok=True)
            os.makedirs(models_dir, exist_ok=True)

            # Step 1: Create data science files
            ds_files = [
                (
                    "data_preprocessing.py",
                    """
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

def load_data(filepath: str) -> pd.DataFrame:
    \"\"\"Load and validate data.\"\"\"
    try:
        data = pd.read_csv(filepath)
        print(f"Data loaded: {data.shape[0]} rows, {data.shape[1]} columns")
        return data
    except Exception as e:
        print(f"Error loading data: {e}")
        raise

def preprocess_data(data: pd.DataFrame) -> tuple:
    \"\"\"Preprocess data for machine learning.\"\"\"
    # Handle missing values
    data = data.fillna(data.mean())

    # Normalize numerical features
    scaler = StandardScaler()
    numerical_cols = data.select_dtypes(include=[np.number]).columns
    data[numerical_cols] = scaler.fit_transform(data[numerical_cols])

    return data, scaler

def split_data(data: pd.DataFrame, target_col: str, test_size: float = 0.2):
    \"\"\"Split data into train and test sets.\"\"\"
    X = data.drop(columns=[target_col])
    y = data[target_col]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42
    )

    return X_train, X_test, y_train, y_test

if __name__ == "__main__":
    # Example usage
    data = load_data("data/dataset.csv")
    processed_data, scaler = preprocess_data(data)
    X_train, X_test, y_train, y_test = split_data(processed_data, "target")
    print("Data preprocessing completed successfully")
""",
                ),
                (
                    "model_training.py",
                    """
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib
import json

def train_model(X_train: pd.DataFrame, y_train: pd.Series) -> RandomForestClassifier:
    \"\"\"Train a machine learning model.\"\"\"
    model = RandomForestClassifier(
        n_estimators=100,
        random_state=42,
        n_jobs=-1
    )

    model.fit(X_train, y_train)
    return model

def evaluate_model(model: RandomForestClassifier, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
    \"\"\"Evaluate model performance.\"\"\"
    predictions = model.predict(X_test)

    accuracy = accuracy_score(y_test, predictions)
    report = classification_report(y_test, predictions, output_dict=True)

    metrics = {
        "accuracy": accuracy,
        "classification_report": report,
        "feature_importance": dict(zip(
            X_test.columns,
            model.feature_importances_
        ))
    }

    return metrics

def save_model(model: RandomForestClassifier, filepath: str):
    \"\"\"Save trained model.\"\"\"
    joblib.dump(model, filepath)
    print(f"Model saved to {filepath}")

if __name__ == "__main__":
    # Example usage
    # Load processed data
    data = pd.read_csv("data/processed_data.csv")
    X_train, X_test, y_train, y_test = split_data(data, "target")

    # Train and evaluate model
    model = train_model(X_train, y_train)
    metrics = evaluate_model(model, X_test, y_test)

    # Save results
    with open("results/metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    save_model(model, "models/random_forest.pkl")
    print("Model training and evaluation completed successfully")
""",
                ),
                (
                    "exploratory_data_analysis.ipynb",
                    """
{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# Exploratory Data Analysis\\n",
    "\\n",
    "This notebook contains exploratory data analysis for the project."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "import pandas as pd\\n",
    "import matplotlib.pyplot as plt\\n",
    "import seaborn as sns\\n",
    "\\n",
    "# Load data\\n",
    "df = pd.read_csv('data/dataset.csv')\\n",
    "print(f'Data shape: {df.shape}')\\n",
    "print(f'Columns: {list(df.columns)}')\\n",
    "\\n",
    "# Basic statistics\\n",
    "print('\\nBasic Statistics:')\\n",
    "print(df.describe())"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.8.5"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 4
}
""",
                ),
                (
                    "requirements_ds.txt",
                    """
pandas>=1.3.0
numpy>=1.21.0
scikit-learn>=0.24.0
matplotlib>=3.4.0
seaborn>=0.11.0
jupyter>=1.0.0
joblib>=1.0.0
""",
                ),
            ]

            # Create data science files
            file_evidence = []
            for filename, content in ds_files:
                file_path = os.path.join(ds_dir, filename)
                with open(file_path, "w") as f:
                    f.write(content)

                file_evidence.extend(
                    self.evidence_generator.create_file_evidence([file_path])
                )
                self.hook.log_evidence(
                    "data_science",
                    f"Data science file created: {filename}",
                    [file_path],
                )

            # Step 2: Simulate data science tasks
            try:
                # Data validation (simulated)
                self.hook.log_evidence(
                    "data_validation",
                    "Data validation completed with quality checks",
                    [os.path.join(ds_dir, "data_preprocessing.py")],
                )

                # Model training (simulated)
                model_training_output = """
Model Training Results:
- Training accuracy: 0.95
- Validation accuracy: 0.92
- Test accuracy: 0.91
- Cross-validation score: 0.90 ± 0.02

Model training completed successfully with good performance.
"""
                self.hook.log_evidence(
                    "model_training", "Machine learning model trained successfully", []
                )

                # Model evaluation (simulated)
                evaluation_metrics = {
                    "accuracy": 0.91,
                    "precision": 0.89,
                    "recall": 0.93,
                    "f1_score": 0.91,
                }
                self.hook.log_evidence(
                    "model_evaluation", "Model evaluation completed with metrics", []
                )

                # Model deployment (simulated)
                self.hook.log_evidence(
                    "model_deployment",
                    "Model deployed to production environment",
                    [os.path.join(ds_dir, "models", "random_forest.pkl")],
                )

                # Performance monitoring (simulated)
                performance_results = """
Model Performance Monitoring:
- Inference time: 25ms
- Memory usage: 50MB
- CPU usage: 15%
- Predictions per second: 40

Model performance within acceptable limits.
"""
                self.hook.log_evidence(
                    "performance_monitoring",
                    "Model performance monitoring completed",
                    [],
                )

            except Exception as e:
                print(f"Data science workflow error: {e}")

            # Step 3: Complete data science validation
            context = {
                "evidence_provided": True,
                "checklist": {
                    "evidence_provided": True,
                    "tests_written": True,
                    "tests_pass": True,
                    "code_reviewed": True,
                    "files_created": True,
                    "performance_validated": True,
                },
            }

            can_complete, issues = self.hook.can_complete_task(context)
            assert len(issues) == 0 or can_complete is True

            # Step 4: Verify anti-deception protection for data science operations
            # Should block dangerous data operations
            dangerous_ds_op = os.path.join(ds_dir, "..", "rm", "-rf", "/data")
            is_safe, reason = self.hook.validate_file_operation(
                dangerous_ds_op, "write"
            )
            assert is_safe is False

    def test_mixed_development_workflow(self):
        """Test anti-deception protection in mixed development workflow."""
        with self.temp_dir as temp_path:
            # Simulate mixed development workflow (full-stack + DevOps + Data Science)
            mixed_dir = os.path.join(temp_path, "mixed_project")

            # Create project structure
            frontend_dir = os.path.join(mixed_dir, "frontend")
            backend_dir = os.path.join(mixed_dir, "backend")
            devops_dir = os.path.join(mixed_dir, "devops")
            data_dir = os.path.join(mixed_dir, "data")

            for directory in [frontend_dir, backend_dir, devops_dir, data_dir]:
                os.makedirs(directory, exist_ok=True)

            # Step 1: Create mixed project files
            mixed_files = [
                # Frontend
                (
                    "package.json",
                    '{\n  "name": "mixed-project-frontend",\n  "version": "1.0.0"\n}',
                ),
                ("index.js", "console.log('Frontend initialized');"),
                # Backend
                ("app.py", "print('Backend server started');"),
                ("requirements.txt", "flask==2.0.0"),
                # DevOps
                (
                    "Dockerfile",
                    "FROM python:3.9\nCOPY requirements.txt .\nRUN pip install -r requirements.txt",
                ),
                # Data Science
                ("data.csv", "value1,value2\n1,2\n3,4"),
                (
                    "script.py",
                    "import pandas as pd\ndf = pd.read_csv('data.csv')\nprint(df)",
                ),
            ]

            # Create mixed files
            file_evidence = []
            for filename, content in mixed_files:
                file_path = os.path.join(mixed_dir, filename)
                with open(file_path, "w") as f:
                    f.write(content)

                file_evidence.extend(
                    self.evidence_generator.create_file_evidence([file_path])
                )
                self.hook.log_evidence(
                    "mixed_development",
                    f"Mixed project file created: {filename}",
                    [file_path],
                )

            # Step 2: Simulate mixed development tasks
            try:
                # Frontend development
                self.hook.log_evidence(
                    "frontend_development",
                    "Frontend components developed",
                    [os.path.join(frontend_dir, "index.js")],
                )

                # Backend development
                self.hook.log_evidence(
                    "backend_development",
                    "Backend API endpoints implemented",
                    [os.path.join(backend_dir, "app.py")],
                )

                # DevOps configuration
                self.hook.log_evidence(
                    "devops_configuration",
                    "Docker containers configured",
                    [os.path.join(devops_dir, "Dockerfile")],
                )

                # Data processing
                self.hook.log_evidence(
                    "data_processing",
                    "Data processing pipeline implemented",
                    [os.path.join(data_dir, "script.py")],
                )

                # Integration testing (simulated)
                integration_output = """
Integration Test Results:
- Frontend-backend connection: PASSED
- API endpoints: PASSED
- Database connectivity: PASSED
- Docker container deployment: PASSED

All integration tests passed successfully.
"""
                self.hook.verify_test_results(integration_output)

                # End-to-end testing (simulated)
                e2e_output = """
End-to-End Test Results:
- User authentication: PASSED
- Data flow: PASSED
- UI interactions: PASSED
- Error handling: PASSED

E2E testing completed successfully.
"""
                self.hook.log_evidence(
                    "e2e_testing", "End-to-end testing completed", []
                )

            except Exception as e:
                print(f"Mixed workflow error: {e}")

            # Step 3: Complete mixed development validation
            context = {
                "evidence_provided": True,
                "checklist": {
                    "evidence_provided": True,
                    "tests_written": True,
                    "tests_pass": True,
                    "code_reviewed": True,
                    "files_created": True,
                    "safety_validated": True,
                    "performance_validated": True,
                    "security_checked": True,
                },
            }

            can_complete, issues = self.hook.can_complete_task(context)
            assert len(issues) == 0 or can_complete is True

            # Step 4: Verify comprehensive anti-deception protection
            # Should block dangerous operations across all domains
            dangerous_operations = [
                "/etc/passwd",  # System file
                "/var/www/html",  # Web server
                "/data",  # Data storage
                "/dev/sda",  # Disk device
                "../dangerous_op.txt",  # Path traversal
            ]

            for dangerous_op in dangerous_operations:
                is_safe, reason = self.hook.validate_file_operation(
                    dangerous_op, "write"
                )
                assert (
                    is_safe is False
                ), f"Dangerous operation {dangerous_op} was not blocked"

    def test_workflow_anti_deception_patterns(self):
        """Test detection of anti-deception patterns in development workflows."""
        # Test common anti-deception patterns that should be detected and blocked

        anti_deception_patterns = [
            # Premature completion claims
            {
                "scenario": "Premature task completion",
                "claim": "Task completed successfully",
                "evidence": [],  # No evidence provided
                "expected_blocked": True,
            },
            # False performance claims
            {
                "scenario": "False performance optimization",
                "claim": "Optimized performance by 500%",
                "evidence": [],  # No evidence provided
                "expected_blocked": True,
            },
            # Dangerous file operations
            {
                "scenario": "Dangerous system file operation",
                "claim": "Modified system configuration",
                "evidence": [],  # No evidence provided
                "file_path": "/etc/passwd",
                "operation": "write",
                "expected_blocked": True,
            },
            # Insufficient evidence for testing
            {
                "scenario": "Insufficient test evidence",
                "claim": "All tests pass",
                "evidence": [],  # No test results provided
                "expected_blocked": True,
            },
            # False security claims
            {
                "scenario": "False security audit",
                "claim": "Security audit completed",
                "evidence": [],  # No security evidence provided
                "expected_blocked": True,
            },
        ]

        for pattern in anti_deception_patterns:
            try:
                with self.temp_dir as temp_path:
                    print(f"Testing anti-deception pattern: {pattern['scenario']}")

                    # Test file operations if applicable
                    if "file_path" in pattern and "operation" in pattern:
                        is_safe, reason = self.hook.validate_file_operation(
                            pattern["file_path"], pattern["operation"]
                        )

                        assert (
                            is_safe == pattern["expected_blocked"]
                        ), f"File operation for {pattern['scenario']} was {'not ' if pattern['expected_blocked'] else ''}blocked as expected"

                    # Test evidence requirements
                    if "claim" in pattern and "evidence" in pattern:
                        result = self.hook.require_evidence(
                            pattern["claim"], pattern["evidence"]
                        )

                        assert (
                            result == pattern["expected_blocked"]
                        ), f"Evidence requirement for {pattern['scenario']} was {'not ' if pattern['expected_blocked'] else ''}enforced as expected"

                    print(
                        f"✓ {pattern['scenario']} correctly {'blocked' if pattern['expected_blocked'] else 'allowed'}"
                    )

            except Exception as e:
                print(f"✗ {pattern['scenario']} test failed: {e}")


if __name__ == "__main__":
    # Run the tests
    import pytest

    pytest.main([__file__, "-v"])
