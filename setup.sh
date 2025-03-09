#!/bin/bash
set -euo pipefail

# Default directories
VENV_DIR=".venv"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if uv is installed
if ! command_exists uv; then
    echo "uv is not installed. Installing uv..."
    if command_exists pip; then
        pip install uv
    else
        echo "Error: Neither uv nor pip is installed. Please install pip first."
        exit 1
    fi
fi

# Create virtual environment
echo "Creating virtual environment..."
if [ -d "$VENV_DIR" ]; then
    echo "Virtual environment already exists. Cleaning..."
    rm -rf "$VENV_DIR"
fi

uv venv "$VENV_DIR"

# Install dependencies
echo "Installing dependencies..."
uv pip install -r requirements.txt

echo
echo "Setup complete! To activate the virtual environment:"
echo "  source .venv/bin/activate"
echo
echo "After activation, you can run the script with:"
echo "  ./scripts/process_binary.py --help"