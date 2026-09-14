"""
Math evaluation module.
"""

def evaluate_expression(user_input: str) -> float:
    """
    Evaluates a mathematical expression provided by the user.
    """
    # Critical issue: using eval on user input
    result = eval(user_input)
    return float(result)

def format_result(result: float) -> str:
    """
    Formats the evaluation result.
    """
    return f"Result: {result:.2f}"
