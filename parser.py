from typing import List, Optional
from lexer import Token, TokenType
from toy_ast import (
    Node, Number, BinaryOp, Variable, Assignment,
    FunctionCall, FunctionDef, If, While, Return
)

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.current_token = tokens[0] if tokens else None

    def error(self, message: str = "Invalid syntax"):
        if self.current_token:
            raise Exception(f"{message} at line {self.current_token.line}, column {self.current_token.column}")
        raise Exception(message)

    def eat(self, token_type: TokenType):
        if self.current_token and self.current_token.type == token_type:
            self.pos += 1
            self.current_token = self.tokens[self.pos] if self.pos < len(self.tokens) else None
        else:
            self.error(f"Expected {token_type}, got {self.current_token.type if self.current_token else 'None'}")

    def parse(self) -> List[Node]:
        nodes = []
        while self.current_token and self.current_token.type != TokenType.EOF:
            if self.current_token.type == TokenType.KEYWORD and self.current_token.value == 'def':
                nodes.append(self.function_definition())
            else:
                nodes.append(self.statement())
        return nodes

    def function_definition(self) -> FunctionDef:
        self.eat(TokenType.KEYWORD)  # eat 'def'
        if not self.current_token or self.current_token.type != TokenType.IDENTIFIER:
            self.error("Expected function name")
        
        name = self.current_token.value
        self.eat(TokenType.IDENTIFIER)
        self.eat(TokenType.LPAREN)
        
        args = []
        while self.current_token and self.current_token.type == TokenType.IDENTIFIER:
            args.append(self.current_token.value)
            self.eat(TokenType.IDENTIFIER)
            if self.current_token.type == TokenType.COMMA:
                self.eat(TokenType.COMMA)
        
        self.eat(TokenType.RPAREN)
        self.eat(TokenType.LBRACE)
        
        body = []
        while self.current_token and self.current_token.type != TokenType.RBRACE:
            body.append(self.statement())
        
        self.eat(TokenType.RBRACE)
        return FunctionDef(name=name, args=args, body=body)

    def statement(self) -> Node:
        if not self.current_token:
            self.error("Unexpected end of input")

        if self.current_token.type == TokenType.KEYWORD:
            if self.current_token.value == 'return':
                return self.return_statement()
            elif self.current_token.value == 'if':
                return self.if_statement()
            elif self.current_token.value == 'while':
                return self.while_statement()

        if self.current_token.type == TokenType.IDENTIFIER:
            if self.tokens[self.pos + 1].type == TokenType.OPERATOR and self.tokens[self.pos + 1].value == '=':
                return self.assignment()
            else:
                expr = self.expr()
                self.eat(TokenType.SEMICOLON)
                return expr

        expr = self.expr()
        self.eat(TokenType.SEMICOLON)
        return expr

    def return_statement(self) -> Return:
        self.eat(TokenType.KEYWORD)  # eat 'return'
        value = self.expr()
        self.eat(TokenType.SEMICOLON)
        return Return(value)

    def if_statement(self) -> If:
        self.eat(TokenType.KEYWORD)  # eat 'if'
        self.eat(TokenType.LPAREN)
        condition = self.expr()
        self.eat(TokenType.RPAREN)
        
        self.eat(TokenType.LBRACE)
        then_body = []
        while self.current_token and self.current_token.type != TokenType.RBRACE:
            then_body.append(self.statement())
        self.eat(TokenType.RBRACE)

        else_body = None
        if self.current_token and self.current_token.type == TokenType.KEYWORD and self.current_token.value == 'else':
            self.eat(TokenType.KEYWORD)
            self.eat(TokenType.LBRACE)
            else_body = []
            while self.current_token and self.current_token.type != TokenType.RBRACE:
                else_body.append(self.statement())
            self.eat(TokenType.RBRACE)

        return If(condition, then_body, else_body)

    def while_statement(self) -> While:
        self.eat(TokenType.KEYWORD)  # eat 'while'
        self.eat(TokenType.LPAREN)
        condition = self.expr()
        self.eat(TokenType.RPAREN)
        
        self.eat(TokenType.LBRACE)
        body = []
        while self.current_token and self.current_token.type != TokenType.RBRACE:
            body.append(self.statement())
        self.eat(TokenType.RBRACE)

        return While(condition, body)

    def assignment(self) -> Assignment:
        name = self.current_token.value
        self.eat(TokenType.IDENTIFIER)
        self.eat(TokenType.OPERATOR)  # eat '='
        value = self.expr()
        self.eat(TokenType.SEMICOLON)
        return Assignment(name, value)

    def expr(self) -> Node:
        node = self.term()

        while self.current_token and self.current_token.type == TokenType.OPERATOR and \
              self.current_token.value in ['+', '-', '<', '>', '==']:
            op = self.current_token.value
            self.eat(TokenType.OPERATOR)
            node = BinaryOp(left=node, operator=op, right=self.term())

        return node

    def term(self) -> Node:
        node = self.factor()

        while self.current_token and self.current_token.type == TokenType.OPERATOR and \
              self.current_token.value in ['*', '/']:
            op = self.current_token.value
            self.eat(TokenType.OPERATOR)
            node = BinaryOp(left=node, operator=op, right=self.factor())

        return node

    def factor(self) -> Node:
        token = self.current_token

        if token.type == TokenType.NUMBER:
            self.eat(TokenType.NUMBER)
            return Number(float(token.value))
        
        elif token.type == TokenType.IDENTIFIER:
            self.eat(TokenType.IDENTIFIER)
            if self.current_token and self.current_token.type == TokenType.LPAREN:
                self.eat(TokenType.LPAREN)
                args = []
                if self.current_token.type != TokenType.RPAREN:
                    args.append(self.expr())
                    while self.current_token.type == TokenType.COMMA:
                        self.eat(TokenType.COMMA)
                        args.append(self.expr())
                self.eat(TokenType.RPAREN)
                return FunctionCall(token.value, args)
            return Variable(token.value)
        
        elif token.type == TokenType.LPAREN:
            self.eat(TokenType.LPAREN)
            node = self.expr()
            self.eat(TokenType.RPAREN)
            return node
        
        self.error("Invalid factor") 