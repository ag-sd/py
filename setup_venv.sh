#! /bin/bash

VENV_DIR="venv"

# Clean up
rm -rf $VENV_DIR

# Create venv dir
mkdir -v -p $VENV_DIR

# Install Python venv
echo "Creating a Python virtual environment"
python3 -m venv $VENV_DIR
source "$VENV_DIR/bin/activate"
echo "Upgrading virtual environment"
python3 -m pip install --upgrade pip

# Install dependencies
echo "Install dependency : PYQT5"
pip install pyqt5
pip install psutil