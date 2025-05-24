from typing import Dict, Any, Optional
import llvmlite.ir as ir
import llvmlite.binding as llvm
from toy_ast import (
    Node, Number, BinaryOp, Variable, Assignment,
    FunctionCall, FunctionDef, If, While, Return
)

class CodeGen:
    def __init__(self):
        self.module = ir.Module(name="toylang_module")
        self.builder = None
        self.func = None
        self.variables: Dict[str, ir.AllocaInstr] = {}
        self.functions: Dict[str, ir.Function] = {}

        # Initialize LLVM
        llvm.initialize()
        llvm.initialize_native_target()
        llvm.initialize_native_asmprinter()

        # Create some basic types we'll need
        self.void_t = ir.VoidType()
        self.int_t = ir.IntType(64)
        self.double_t = ir.DoubleType()
        self.bool_t = ir.IntType(1)

    def _create_entry_block_alloca(self, name: str) -> ir.AllocaInstr:
        """Create an alloca instruction in the entry block of the current function"""
        # Get the entry block
        entry_block = self.func.entry_basic_block
        # Create a builder positioned at the start of the entry block
        builder = ir.IRBuilder()
        builder.position_at_start(entry_block)
        # Create the alloca
        return builder.alloca(self.double_t, size=None, name=name)

    def generate_code(self, node: Node) -> Optional[ir.Value]:
        if isinstance(node, Number):
            return ir.Constant(self.double_t, float(node.value))

        elif isinstance(node, BinaryOp):
            left = self.generate_code(node.left)
            right = self.generate_code(node.right)

            if node.operator == '+':
                return self.builder.fadd(left, right, 'addtmp')
            elif node.operator == '-':
                return self.builder.fsub(left, right, 'subtmp')
            elif node.operator == '*':
                return self.builder.fmul(left, right, 'multmp')
            elif node.operator == '/':
                return self.builder.fdiv(left, right, 'divtmp')
            elif node.operator in ['<', '>', '==']:
                cmp = self.builder.fcmp_ordered(
                    {'<': '<', '>': '>', '==': '=='}[node.operator],
                    left, right, 'cmptmp'
                )
                return self.builder.uitofp(cmp, self.double_t, 'booltmp')

        elif isinstance(node, Variable):
            var = self.variables.get(node.name)
            if var is None:
                raise Exception(f"Unknown variable: {node.name}")
            return self.builder.load(var, node.name)

        elif isinstance(node, Assignment):
            if node.name not in self.variables:
                self.variables[node.name] = self._create_entry_block_alloca(node.name)
            
            val = self.generate_code(node.value)
            self.builder.store(val, self.variables[node.name])
            return val

        elif isinstance(node, FunctionCall):
            callee = self.module.get_global(node.name)
            if callee is None:
                raise Exception(f"Unknown function: {node.name}")

            args = [self.generate_code(arg) for arg in node.arguments]
            return self.builder.call(callee, args, 'calltmp')

        elif isinstance(node, FunctionDef):
            # Create function type
            func_type = ir.FunctionType(self.double_t, [self.double_t] * len(node.args))
            
            # Create function
            func = ir.Function(self.module, func_type, name=node.name)
            self.functions[node.name] = func

            # Create entry block and position builder
            entry_block = func.append_basic_block('entry')
            
            # Save current state
            old_builder = self.builder
            old_func = self.func
            old_variables = self.variables.copy()

            # Update state for new function
            self.func = func
            self.variables.clear()

            # Create allocas for arguments at the start of the entry block
            for arg, arg_name in zip(func.args, node.args):
                arg.name = arg_name
                alloca = self._create_entry_block_alloca(arg_name)
                self.variables[arg_name] = alloca

            # Position builder at the end of the entry block
            self.builder = ir.IRBuilder(entry_block)

            # Store arguments
            for arg, arg_name in zip(func.args, node.args):
                self.builder.store(arg, self.variables[arg_name])

            # Generate code for function body
            for stmt in node.body:
                self.generate_code(stmt)

            # Add a return 0.0 if the function doesn't have a return statement
            if not entry_block.is_terminated:
                self.builder.ret(ir.Constant(self.double_t, 0.0))

            # Restore state
            self.builder = old_builder
            self.func = old_func
            self.variables = old_variables

            return func

        elif isinstance(node, If):
            cond_val = self.generate_code(node.condition)
            
            # Convert condition to boolean
            cond_val = self.builder.fcmp_ordered('!=', cond_val, 
                ir.Constant(self.double_t, 0.0), 'ifcond')

            # Create blocks for then, else, and merge
            then_bb = self.func.append_basic_block('then')
            else_bb = self.func.append_basic_block('else')
            merge_bb = self.func.append_basic_block('ifcont')

            # Branch based on condition
            self.builder.cbranch(cond_val, then_bb, else_bb)

            # Generate 'then' block
            self.builder.position_at_start(then_bb)
            then_val = None
            for stmt in node.then_body:
                then_val = self.generate_code(stmt)
            if not then_bb.is_terminated:
                self.builder.branch(merge_bb)

            # Generate 'else' block
            self.builder.position_at_start(else_bb)
            else_val = None
            if node.else_body:
                for stmt in node.else_body:
                    else_val = self.generate_code(stmt)
            if not else_bb.is_terminated:
                self.builder.branch(merge_bb)

            # Move to merge block
            self.builder.position_at_start(merge_bb)

            # If both branches return a value, we need a phi node
            if then_val is not None and else_val is not None:
                phi = self.builder.phi(self.double_t, 'iftmp')
                phi.add_incoming(then_val, then_bb)
                phi.add_incoming(else_val, else_bb)
                return phi
            return None

        elif isinstance(node, While):
            # Create blocks
            cond_bb = self.func.append_basic_block('while.cond')
            body_bb = self.func.append_basic_block('while.body')
            end_bb = self.func.append_basic_block('while.end')

            # Branch to condition block
            self.builder.branch(cond_bb)

            # Generate condition block
            self.builder.position_at_start(cond_bb)
            cond_val = self.generate_code(node.condition)
            cond_val = self.builder.fcmp_ordered('!=', cond_val,
                ir.Constant(self.double_t, 0.0), 'whilecond')
            self.builder.cbranch(cond_val, body_bb, end_bb)

            # Generate body block
            self.builder.position_at_start(body_bb)
            for stmt in node.body:
                self.generate_code(stmt)
            self.builder.branch(cond_bb)

            # Move to end block
            self.builder.position_at_start(end_bb)

        elif isinstance(node, Return):
            val = self.generate_code(node.value)
            self.builder.ret(val)

        return None

    def create_ir(self, ast: list) -> str:
        # Generate code for all nodes
        for node in ast:
            self.generate_code(node)

        # Make sure we have a return in main
        if 'main' in self.functions:
            main_func = self.functions['main']
            if not main_func.blocks[-1].is_terminated:
                self.builder = ir.IRBuilder(main_func.blocks[-1])
                self.builder.ret(ir.Constant(self.double_t, 0.0))

        return str(self.module) 