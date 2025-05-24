# ToyLang Compiler

A simple compiler implementation using Python and LLVM (via llvmlite) applied to fibonacci calculations.

## Overview

ToyLang is a minimal programming language that supports:
- Basic arithmetic operations
- Variable declarations
- If-else conditionals
- While loops
- Function definitions and calls

## Project Structure

- `lexer.py`: Tokenizes the input source code
- `parser.py`: Parses tokens into an Abstract Syntax Tree (AST)
- `toy_ast.py`: Defines AST node classes
- `codegen.py`: Generates LLVM IR from the AST
- `main.py`: Main compiler driver
- `sample.toy`: Example programs in ToyLang
- `mise.toml`: Project configuration for mise and uv package management
- `init.sh`: Development environment setup script

## Language Features

Example ToyLang syntax:
```
def fibonacci(n) {
    if (n < 2) {
        return n;
    }
    return fibonacci(n-1) + fibonacci(n-2);
}

def main() {
    return fibonacci(10);
}
```
Create a new ToyLang file with `my_file.toy`

## Requirements

- macOS
- Homebrew
- Python 3.8+
- [mise](https://mise.jdx.dev/) for environment management

## Quick Start

1. Initialize the development environment:
```bash
./init.sh
```
This script will:
- Install LLVM if not already installed
- Set up necessary environment variables
- Create a Python virtual environment
- Install all required dependencies

2. Activate Python virtual environment:
```bash
source .venv/bin/activate
```

3. Run the example program:
```bash
python main.py sample.toy
```

## Development

After the initial setup, your virtual environment will be activated and ready to use. If you need to set up the environment again (e.g., after restarting your terminal), just run `./init.sh`. 