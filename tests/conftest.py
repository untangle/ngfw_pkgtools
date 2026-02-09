"""
Pytest configuration and shared fixtures for ngfw_pkgtools tests
"""

import os
import sys

# Add the parent directory to the path so we can import lib modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
