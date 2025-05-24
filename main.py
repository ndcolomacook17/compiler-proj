#!/usr/bin/env python3
import sys
import traceback
import llvmlite.binding as llvm

from lexer import Lexer
from parser import Parser
from codegen import CodeGen

def compile_and_run(source_code: str) -> float:
    try:
        # Initialize lexer and get tokens
        lexer = Lexer(source_code)
        tokens = lexer.tokenize()
        print("Lexical analysis completed")

        # Parse tokens into AST
        parser = Parser(tokens)
        ast = parser.parse()
        print("Parsing completed")

        # Generate LLVM IR
        codegen = CodeGen()
        llvm_ir = codegen.create_ir(ast)
        print("LLVM IR generated")
        print(llvm_ir)  # Print the generated IR for debugging
        
        # Initialize LLVM components
        llvm.initialize()
        llvm.initialize_native_target()
        llvm.initialize_native_asmprinter()

        # Create module and compile
        mod = llvm.parse_assembly(llvm_ir)
        mod.verify()

        # Create execution engine
        target = llvm.Target.from_default_triple()
        target_machine = target.create_target_machine()
        backing_mod = llvm.parse_assembly("")
        engine = llvm.create_mcjit_compiler(backing_mod, target_machine)
        
        # Add the module and make sure it is ready for execution
        engine.add_module(mod)
        engine.finalize_object()

        # Get the function pointer to our compiled function
        func_ptr = engine.get_function_address("main")

        # Cast the pointer to a Python callable using CFUNCTYPE
        from ctypes import CFUNCTYPE, c_double
        cfunc = CFUNCTYPE(c_double)(func_ptr)
        
        # Call the function
        result = cfunc()
        return float(result)
    except Exception as e:
        print(f"Error: {str(e)}")
        print("Traceback:")
        traceback.print_exc()
        raise

def main():
    if len(sys.argv) != 2:
        print("Usage: python main.py <source_file>")
        sys.exit(1)

    source_file = sys.argv[1]
    try:
        with open(source_file, 'r') as f:
            source_code = f.read()
        
        result = compile_and_run(source_code)
        print(f"Result: {result}")

    except FileNotFoundError:
        print(f"Error: Could not find file '{source_file}'")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 