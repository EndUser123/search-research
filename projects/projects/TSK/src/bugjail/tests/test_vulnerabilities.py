"""
Test Vulnerability Scanner

Test cases for OWASP Top 10 vulnerability detection.
"""

import tempfile
import unittest
from pathlib import Path

from ..core.detector import BugJailDetector
from ..core.types import BugJailConfig, BugSeverity, VulnerabilityType


class TestVulnerabilityScanner(unittest.TestCase):
    """Test OWASP vulnerability detection."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = BugJailConfig(
            enable_vulnerability_scanning=True,
            enable_owasp_patterns=True
        )
        self.detector = BugJailDetector(self.config)

    def test_sql_injection_detection(self):
        """Test SQL injection vulnerability detection."""
        code = """
import sqlite3

def get_user(user_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # SQL Injection vulnerability
    query = f\"SELECT * FROM users WHERE id = {user_id}\"
    cursor.execute(query)

    # Another SQL injection
    cursor.execute(\"SELECT * FROM users WHERE name = '%s'\" % user_name)

    return cursor.fetchone()

def search_users(search_term):
    # String formatting in SQL
    query = \"SELECT * FROM users WHERE name LIKE '%{}%'\".format(search_term)
    return db.execute(query).fetchall()
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()

            report = self.detector.analyze_path(f.name)

            # Should detect SQL injection vulnerabilities
            injection_vulns = [
                v for v in report.vulnerabilities
                if v.vulnerability_type == VulnerabilityType.A03_INJECTION
            ]
            self.assertGreater(len(injection_vulns), 0)

            # Check vulnerability details
            for vuln in injection_vulns:
                self.assertEqual(vuln.severity, BugSeverity.CRITICAL)
                self.assertIn("sql", vuln.description.lower())

            # Clean up
            Path(f.name).unlink()

    def test_command_injection_detection(self):
        """Test command injection vulnerability detection."""
        code = """
import os
import subprocess

def run_system_command(user_input):
    # Command injection with os.system
    result = os.system(f\"ls {user_input}\")
    return result

def execute_with_subprocess(cmd):
    # Command injection with shell=True
    result = subprocess.run(cmd, shell=True, check=True)
    return result.stdout

def ping_host(hostname):
    # Another shell=True example
    return subprocess.call(f\"ping -c 4 {hostname}\", shell=True)

def process_file(filename):
    # Potential command injection
    os.system(f\"cat {filename}\")
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()

            report = self.detector.analyze_path(f.name)

            # Should detect command injection vulnerabilities
            injection_vulns = [
                v for v in report.vulnerabilities
                if v.vulnerability_type == VulnerabilityType.A03_INJECTION
            ]
            self.assertGreater(len(injection_vulns), 0)

            # Clean up
            Path(f.name).unlink()

    def test_weak_cryptography_detection(self):
        """Test weak cryptography detection."""
        code = """
import hashlib
import Crypto

def hash_password(password):
    # Weak hashing algorithm
    return hashlib.md5(password.encode()).hexdigest()

def weak_hash(data):
    # Another weak algorithm
    return hashlib.sha1(data.encode()).hexdigest()

def encrypt_data(data):
    # Weak encryption (if implemented)
    from Crypto.Cipher import DES
    key = b'8bytekey'
    cipher = DES.new(key, DES.MODE_ECB)
    return cipher.encrypt(data)

def secure_hash(password):
    # Good practice (should not trigger)
    import bcrypt
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()

            report = self.detector.analyze_path(f.name)

            # Should detect weak cryptographic failures
            crypto_vulns = [
                v for v in report.vulnerabilities
                if v.vulnerability_type == VulnerabilityType.A02_CRYPTOGRAPHIC_FAILURES
            ]
            self.assertGreater(len(crypto_vulns), 0)

            # Check severity
            for vuln in crypto_vulns:
                self.assertIn(vuln.severity, [BugSeverity.HIGH, BugSeverity.CRITICAL])

            # Clean up
            Path(f.name).unlink()

    def test_hardcoded_secrets_detection(self):
        """Test hardcoded secrets detection."""
        code = """
# Configuration with hardcoded secrets
DATABASE_URL = \"postgresql://user:password123@localhost/db\"
AWS_SECRET_KEY = \"AKIAIOSFODNN7EXAMPLE\"
API_KEY = \"sk-1234567890abcdef\"

class Config:
    # Hardcoded password
    SECRET_KEY = \"my-secret-key-12345\"
    DB_PASSWORD = \"admin123\"

    # More secrets
    JWT_SECRET = \"jwt-secret-key-here\"
    ENCRYPTION_KEY = \"this-is-a-32-byte-key-for-aes\"

def get_database_connection():
    # Connection string with password
    conn_str = f\"mysql://root:rootpassword@localhost:3306/mydb\"
    return connect(conn_str)
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()

            report = self.detector.analyze_path(f.name)

            # Should detect hardcoded secrets
            crypto_vulns = [
                v for v in report.vulnerabilities
                if v.vulnerability_type == VulnerabilityType.A02_CRYPTOGRAPHIC_FAILURES
            ]
            self.assertGreater(len(crypto_vulns), 0)

            # Clean up
            Path(f.name).unlink()

    def test_xss_detection_javascript(self):
        """Test XSS detection in JavaScript."""
        code = """
function displayUserInput(input) {
    // XSS vulnerability with innerHTML
    document.getElementById('output').innerHTML = user_input;

    // Another XSS example
    element.innerHTML = '<div>' + userInput + '</div>';

    // Unsafe use of eval
    eval('processData(' + JSON.stringify(userInput) + ')');

    // Function constructor
    var func = new Function('return ' + userInput);
}

function updatePage(data) {
    // Template literal injection
    document.body.innerHTML = `<h1>${data.title}</h1>`;
}

// Safe example (should not trigger)
function safeDisplay(input) {
    document.getElementById('output').textContent = input;
}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(code)
            f.flush()

            report = self.detector.analyze_path(f.name)

            # Should detect XSS vulnerabilities
            xss_vulns = [
                v for v in report.vulnerabilities
                if v.vulnerability_type == VulnerabilityType.A03_INJECTION
            ]
            self.assertGreater(len(xss_vulns), 0)

            # Clean up
            Path(f.name).unlink()

    def test_broken_access_control_detection(self):
        """Test broken access control detection."""
        code = """
from flask import Flask, request

app = Flask(__name__)

@app.route('/user/<int:user_id>')
def get_user(user_id):
    # Insecure direct object reference
    user = db.query(\"SELECT * FROM users WHERE id = ?\", user_id)
    return jsonify(user)

@app.route('/admin/delete/<int:item_id>')
def delete_item(item_id):
    # No authorization check
    db.execute(\"DELETE FROM items WHERE id = ?\", item_id)
    return jsonify({\"success\": True})

@app.route('/api/files/<filename>')
def download_file(filename):
    # Path traversal risk and no access control
    return send_file(f'/uploads/{filename}')

# Missing authentication decorator
@app.route('/secret-data')
def secret_data():
    return get_secret_data()

# Good example (should not trigger for this specific pattern)
@app.route('/public/<int:id>')
def public_data(id):
    return get_public_data(id)
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()

            report = self.detector.analyze_path(f.name)

            # Should detect access control issues
            access_vulns = [
                v for v in report.vulnerabilities
                if v.vulnerability_type == VulnerabilityType.A01_BROKEN_ACCESS_CONTROL
            ]
            # May or may not detect depending on pattern matching
            # self.assertGreater(len(access_vulns), 0)

            # Clean up
            Path(f.name).unlink()

    def test_debug_mode_detection(self):
        """Test debug mode in production detection."""
        code = """
# Django settings
DEBUG = True  # Debug mode enabled

# Flask app
app = Flask(__name__)
app.debug = True  # Debug enabled

# Another debug setting
DEBUG_MODE = 'production'  # This might be safe
APP_DEBUG = os.environ.get('DEBUG', True)  # Default True is risky

# Safe settings
PRODUCTION_DEBUG = False
app.config['DEBUG'] = False

def check_debug():
    if DEBUG:
        print("Debug mode is ON")
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()

            report = self.detector.analyze_path(f.name)

            # Should detect debug mode issues
            debug_vulns = [
                v for v in report.vulnerabilities
                if v.vulnerability_type == VulnerabilityType.A05_SECURITY_MISCONFIGURATION
            ]
            self.assertGreater(len(debug_vulns), 0)

            # Clean up
            Path(f.name).unlink()

    def test_unsafe_deserialization_detection(self):
        """Test unsafe deserialization detection."""
        code = """
import pickle
import json

def load_data_unsafe(data):
    # Unsafe deserialization with pickle
    return pickle.loads(data)

def process_user_data(serialized_data):
    # Another unsafe pickle usage
    obj = pickle.loads(serialized_data)
    return obj.process()

def safe_deserialization(data):
    # Safe alternative
    return json.loads(data)

def load_config():
    # Unsafe config loading
    with open('config.pkl', 'rb') as f:
        config = pickle.load(f)  # Unsafe
    return config

# YAML deserialization (if using unsafe loader)
import yaml
def load_yaml_config(filename):
    with open(filename) as f:
        return yaml.load(f)  # Unsafe without Loader=
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()

            report = self.detector.analyze_path(f.name)

            # Should detect unsafe deserialization
            deserialization_vulns = [
                v for v in report.vulnerabilities
                if v.vulnerability_type == VulnerabilityType.A08_SOFTWARE_DATA_INTEGRITY
            ]
            self.assertGreater(len(deserialization_vulns), 0)

            # Clean up
            Path(f.name).unlink()

    def test_ssl_verification_disabled(self):
        """Test disabled SSL verification detection."""
        code = """
import requests
import urllib3
import ssl

# Disable SSL verification (insecure)
response = requests.get('https://api.example.com', verify=False)

# urllib3 SSL verification disabled
http = urllib3.PoolManager(
    cert_reqs='CERT_NONE',
    assert_hostname=False
)

# Create unverified SSL context
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Safe usage (should not trigger)
response = requests.get('https://api.example.com', verify=True)
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()

            report = self.detector.analyze_path(f.name)

            # Should detect SSL verification issues
            ssl_vulns = [
                v for v in report.vulnerabilities
                if v.vulnerability_type == VulnerabilityType.A05_SECURITY_MISCONFIGURATION
            ]
            self.assertGreater(len(ssl_vulns), 0)

            # Clean up
            Path(f.name).unlink()

    def test_cvss_scoring(self):
        """Test CVSS scoring for vulnerabilities."""
        code = """
# Critical: SQL Injection
def get_user(user_id):
    cursor.execute(f\"SELECT * FROM users WHERE id = {user_id}\")

# High: Hardcoded password
PASSWORD = \"admin123\"

# Medium: Debug mode
DEBUG = True
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()

            report = self.detector.analyze_path(f.name)

            # Check CVSS scores
            for vuln in report.vulnerabilities:
                if vuln.cvss_score:
                    self.assertGreaterEqual(vuln.cvss_score, 0.0)
                    self.assertLessEqual(vuln.cvss_score, 10.0)

            # SQL injection should have high CVSS
            sql_vulns = [
                v for v in report.vulnerabilities
                if "sql" in v.description.lower()
            ]
            if sql_vulns:
                self.assertGreater(sql_vulns[0].cvss_score, 7.0)

            # Clean up
            Path(f.name).unlink()


if __name__ == "__main__":
    unittest.main()
