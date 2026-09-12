import argparse 
from decimal import Decimal
import math

"""
potential future ideas: 
- expand new function parsing to unary operators to avoid need for UNARY_CONCAT_OTHER
- refactor by integrating oop into algorithms 
- clean up code
- add option to use radians in trig functions
- add functions that accept more than one argument
- make debug message indentation more accurate
- fix modular functionality
"""

# Create argparse fields
PARSER = argparse.ArgumentParser(description = 'Evaluate a mathematical expression.')
PARSER.add_argument('-e', '--expression', help = 'The expression to evaluate.')
PARSER.add_argument('-d', '--debug', action = 'store_const', const = 'true', help = 'Whether or not debug mode should be turned on (true/false).')
PARSER.add_argument('-r', '--round', help = 'How many decimal places to round output to (defaults to 3 and can be negative).', default = 3)
ARGS = PARSER.parse_args()

# Initialize instance options
DEBUG = True if ARGS.debug else False
ROUND_OUTPUT_TO = int(ARGS.round)

# Define basic operators and their operations
POSITIVE_OPERATIONS = {
    '+' : lambda a, b: a + b,
    '-' : lambda a, b: a - b,
    '*' : lambda a, b: a * b,
    '**' : lambda a, b: a ** b,
    '^' : lambda a, b: a ** b,
    '/' : lambda a, b: a / b,
    '//' : lambda a, b: a // b,
    '%' : lambda a, b: a % b,
    '!' : lambda a: a * POSITIVE_OPERATIONS['!'](a - 1) if a > 1 else 1
}

# Identify which operators are unary
UNARY_ALONE_OPERATORS = ['!']

# Create new operator instances to account for instances where an unary operator is followed by another operator (e.g. '3!+4')
UNARY_CONCAT_OTHER = []

for operator in UNARY_ALONE_OPERATORS:
    UNARY_CONCAT_OTHER.extend([operator + op for op in POSITIVE_OPERATIONS if op not in UNARY_ALONE_OPERATORS])

UNARY_OPERATORS = UNARY_ALONE_OPERATORS + UNARY_CONCAT_OTHER

UNARY_CONCAT_OPERATIONS = {symbol: lambda a, b, symbol=symbol: POSITIVE_OPERATIONS[symbol[1]](POSITIVE_OPERATIONS[symbol[0]](a), b) for symbol in UNARY_CONCAT_OTHER}

# Create new operator instances to account for instances where an operator is followed by an unary '-' (e.g. '3*-4')
NEGATIVE_OPERATIONS = {symbol + '-': lambda a, b, symbol=symbol: POSITIVE_OPERATIONS[symbol](a, -b) for symbol in POSITIVE_OPERATIONS if symbol not in UNARY_OPERATORS}

# Define some functions and their outputs
FUNCTIONS = { # implement min max 
    'sin' : lambda a: Decimal(math.sin(a*Decimal(math.pi)/180)),
    'cos' : lambda a: Decimal(math.cos(a*Decimal(math.pi)/180)),
    'tan' : lambda a: Decimal(math.tan(a*Decimal(math.pi)/180)),
    'sqrt' : lambda a: Decimal(math.sqrt(a))
}

# For expression parsing, define a list of every character present in each possible function call
FUNCTION_CHARS = []

for func in FUNCTIONS:
    FUNCTION_CHARS.extend(list(func))

# Combine all of the defined operators and their operations into one lookup table
OPERATIONS = POSITIVE_OPERATIONS | NEGATIVE_OPERATIONS | UNARY_CONCAT_OPERATIONS | FUNCTIONS

# Define an order of operations
PEMDAS = [
    ('!'),
    ('^', '**'),
    ('*', '/', '//', '%'), 
    ('+', '-')
]

# Procedurally add the operators created to account for operators followed by the unary '-'
for index, precedence in enumerate(PEMDAS):
    newops = [item for item in precedence]

    for op in precedence:
        if op in UNARY_ALONE_OPERATORS:
            for sub_op in POSITIVE_OPERATIONS:
                if sub_op not in UNARY_ALONE_OPERATORS:
                    newops.append(op + sub_op)
        else:
            newops.append(op + "-")
    
    PEMDAS[index] = tuple(newops)

# For expression parsing, define a list with every operator listed in the order of operations
OPERATORS_IN_PEMDAS = []

for precedence in PEMDAS:
    OPERATORS_IN_PEMDAS.extend(precedence)

# Insert the defined functions into the highest possible precedence in the order of operations
PEMDAS.insert(0, tuple(FUNCTIONS.keys()))

# For expression parsing, define a list of characters that could be in a valid number
DIGITS = "1234567890."

# For expression parsing, define a set of legal characters that any expression can be made up of
VALID_CHARS = set(OPERATIONS) | set(DIGITS) | {'(', ')'} | set(FUNCTION_CHARS)

# Print a standardized debug message to the console
def debug_message(*args, indent = 0):
    if DEBUG:
        message = ' '.join([str(item) for item in args])

        print('[DEBUG]', ' ' * indent * 2, message)

# Return a list of strings composed of characters from POSSIBLE_CHARS in STRING
def find_phrases(STRING, POSSIBLE_CHARS):
    phrases = ['']

    for char in STRING:
        if char in POSSIBLE_CHARS:
            phrases[-1] += char
        else:
            phrases.append('')

    for _ in range(phrases.count('')):
        phrases.remove('')

    return phrases

# Raise errors if the provided expression is obviously invalid
def validate_expression(EXPRESSION, EXPRESSION_OPERATIONS, EXPRESSION_NUMBERS):
    if not set(EXPRESSION) <= VALID_CHARS:
        raise Exception("INVALID CHARACTERS DETECTED")

    for item in EXPRESSION_OPERATIONS:
        if len(item) > 1 and not (item in OPERATIONS or item in UNARY_OPERATORS or item in FUNCTIONS) :
            raise Exception("INVALID FUNCTION / OPERATOR")

        if item not in OPERATORS_IN_PEMDAS:
            raise Exception("FUNCTION / OPERATOR NOT IN ORDER OF OPERATIONS")

    if not EXPRESSION.count('(') == EXPRESSION.count(')'):
        raise Exception("MISMATCHED PARENTHESES")

    NUM_UNARY_OPERATORS = sum(EXPRESSION_OPERATIONS.count(operation) for operation in UNARY_ALONE_OPERATORS)
    NUM_FUNCTIONS = sum(EXPRESSION_OPERATIONS.count(operation) for operation in FUNCTIONS)

    if not len(EXPRESSION_NUMBERS) - len(EXPRESSION_OPERATIONS) + NUM_UNARY_OPERATORS + NUM_FUNCTIONS == 1:
        raise Exception("WRONG RATIO OF NUMBERS TO OPERATORS")

# Return a list of the numbers and operations in a given expression
def parse_expression(expression):
    expression = expression.strip(" \'\"")

    expression = list(expression)

    insertions = 0
    exp_copy = expression[:]

    for index, char in enumerate(exp_copy[:-1]):
        if char == '-' and (index == 0 or exp_copy[index - 1] == '('):
                expression.insert(index + insertions, '0')
                insertions += 1

    expression = ''.join(expression)

    expression_numbers = find_phrases(expression, DIGITS)
    expression_operations = find_phrases(expression, list(OPERATIONS.keys()) + FUNCTION_CHARS)

    debug_message('parse_expression:', expression, expression_numbers, expression_operations, indent = 4)

    for i in range(len(expression_numbers)):
        expression_numbers[i] = Decimal(expression_numbers[i])

    validate_expression(expression, expression_operations, expression_numbers)
    
    return expression_numbers, expression_operations

# Safely compute and return the result of an operation and its inputs
def perform_operation(OPERATION, A, B=None):
    debug_message("perform_operation:", OPERATION, A, B, indent=6)

    OPERATION = OPERATION.strip()

    A = Decimal(str(A).strip())

    if B:
        B = Decimal(str(B).strip())

        result = OPERATIONS[OPERATION](A, B)
    else:
        result = OPERATIONS[OPERATION](A)

    return f'{result:.{len(str(result))}f}'

# Completely simplify and return the result of an expression given lists of its numbers and operations
def simplify(expression_numbers, expression_operations):
    debug_message("simplify:", expression_numbers, expression_operations, indent = 5)

    for precedence in PEMDAS:
        for index, operator in enumerate(expression_operations):
            if operator in precedence:
                if operator in set(UNARY_ALONE_OPERATORS) | set(FUNCTIONS):
                    num = perform_operation(operator, expression_numbers[index])
                else:
                    num = perform_operation(operator, expression_numbers[index], expression_numbers[index + 1])

                    expression_numbers.pop(index + 1)

                expression_numbers[index] = num
                expression_operations.pop(index)

                return simplify(expression_numbers, expression_operations)

    return expression_numbers[0]

# Convert a basic (no parentheses) expression to lists of its numbers and operations, and return the simplified result
def evaluate_basic(EXPRESSION):
    EXPRESSION_NUMBERS, EXPRESSION_OPERATIONS = parse_expression(EXPRESSION)
    return simplify(EXPRESSION_NUMBERS, EXPRESSION_OPERATIONS)

# Recursively simplify instances of parentheses in a given expression and return the result
def traverse_parentheses(expression):
    debug_message('traverse_parentheses:', expression, indent = 2)

    memory = {}
    depth = 0

    for index, char in enumerate(expression):
        if char == '(':
            depth += 1
            memory[depth] = index

        if char == ')':
            open_index = memory[depth]
            close_index = index

            return traverse_parentheses(expression[:open_index] + str(traverse_parentheses(expression[open_index + 1:close_index])) + expression[close_index + 1:])

    expression = resolve_functions(expression)

    return evaluate_basic(expression)

# Recursively resolve any function calls in a given expression and return the result
def resolve_functions(expression):
    debug_message('resolve_functions:', expression, indent = 3)

    EXPRESSION_FUNCTIONS = find_phrases(expression, FUNCTION_CHARS)

    if not EXPRESSION_FUNCTIONS:
        return expression

    call = EXPRESSION_FUNCTIONS[0]
    call_contents = ''

    call_index = expression.index(call)
    contents_start_index = call_index + len(call)

    for char in expression[contents_start_index:]:
        if char not in DIGITS + '-':
            break

        call_contents += char

    call_length = len(call) + len(call_contents)

    if len(EXPRESSION_FUNCTIONS) == 1:
        result = perform_operation(call, call_contents)

        return expression[:call_index] + str(result) + expression[call_index + call_length:]

    return resolve_functions(expression[:call_index] + str(resolve_functions(call + call_contents)) + expression[call_index + call_length:])

# Preprocess an expression (e.g. insert implied multiplication operators in cases such as '4(3)'), evaluate the processed expression, and return the result
def evaluate(expression):
    debug_message('evaluate:', expression, indent = 1)

    expression = list(expression)

    insertions = 0
    exp_copy = expression[:]

    for index in range(len(exp_copy) - 1):
        char = exp_copy[index]
        next_char = exp_copy[index + 1]

        if (char in list(DIGITS) + UNARY_OPERATORS and next_char in ['('] + FUNCTION_CHARS) or (char == ')' and next_char in list(DIGITS) + FUNCTION_CHARS) or (char == ')' and next_char == '('): # Check cases: n(, )n, )(
            expression.insert(index + 1 + insertions, '*')
            insertions += 1            

    expression = ''.join(expression)

    return traverse_parentheses(expression)

# Completely simplify an expression and format the answer for the user before returning the result
def find_and_format_answer(expression):
    debug_message('find_and_format_answer:', expression)

    result = Decimal(evaluate(expression))

    result = round(result, ROUND_OUTPUT_TO)

    result = Decimal(result).normalize()

    return result

if __name__ == '__main__':
    # If an expression was provided in the script's arguments, evaluate and exit the script
    if ARGS.expression:
        try:
            print(find_and_format_answer(ARGS.expression))
        except Exception as ERROR:
            print(f"\nGenius caused {ERROR} error\nDon't be sorry. Be better.\n")

        exit(0)

    # Otherwise, keep asking for and evaluating expressions until the user closes the program
    else:
        while True:
            try:
                EXPRESSION = input('Input expression: ')

                if EXPRESSION in ['exit', 'close']:
                    break

                print(f'\n{find_and_format_answer(EXPRESSION)}\n')

            except Exception as ERROR:
                print(f"\nGenius caused {ERROR} error\nDon't be sorry. Be better.\n")
