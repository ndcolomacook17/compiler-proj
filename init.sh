#!/bin/zsh

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "Homebrew not found. Please install Homebrew first."
    echo "Visit https://brew.sh for installation instructions."
    exit 1
fi

# Check if LLVM is installed, install if not
if ! brew list llvm &> /dev/null; then
    echo "Installing LLVM..."
    brew install llvm
fi

# Set up LLVM environment variables
export PATH="/opt/homebrew/opt/llvm/bin:$PATH"
export LDFLAGS="-L/opt/homebrew/opt/llvm/lib"
export CPPFLAGS="-I/opt/homebrew/opt/llvm/include"

# Clean up any existing virtual environment
if [ -d ".venv" ]; then
    echo "Removing existing virtual environment..."
    rm -rf .venv
fi

# Create and activate new virtual environment
echo "Creating new virtual environment..."
uv venv .venv
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
uv pip install -r requirements.txt

echo "\nSetup complete! 🎉"
echo "Virtual environment is now activated and ready to use."
echo "Try running: source .venv/bin/activate && python main.py sample.toy" 