#!/usr/bin/env python3
"""
Simple entry point for the Test Automation Orchestrator.
This script provides easy access to the main CLI from the project root.
"""

import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import and run the main CLI
from main import cli

if __name__ == '__main__':
    cli()