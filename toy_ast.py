from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Node:
    pass

@dataclass
class Number(Node):
    value: float

@dataclass
class BinaryOp(Node):
    left: Node
    operator: str
    right: Node

@dataclass
class Variable(Node):
    name: str

@dataclass
class Assignment(Node):
    name: str
    value: Node

@dataclass
class FunctionCall(Node):
    name: str
    arguments: List[Node]

@dataclass
class FunctionDef(Node):
    name: str
    args: List[str]
    body: List[Node]
    return_stmt: Optional[Node] = None

@dataclass
class If(Node):
    condition: Node
    then_body: List[Node]
    else_body: Optional[List[Node]] = None

@dataclass
class While(Node):
    condition: Node
    body: List[Node]

@dataclass
class Return(Node):
    value: Node 