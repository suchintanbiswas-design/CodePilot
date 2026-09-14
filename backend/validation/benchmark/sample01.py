"""
Utility functions for math operations.
Provides clean and safe implementations of common math helpers.
"""

def get_gcd(a: int, b: int) -> int:
    """Calculate the Greatest Common Divisor of a and b."""
    a, b = abs(a), abs(b)
    while b:
        a, b = b, a % b
    return a

def get_lcm(a: int, b: int) -> int:
    """Calculate the Least Common Multiple of a and b."""
    if a == 0 or b == 0:
        return 0
    return abs(a * b) // get_gcd(a, b)

def is_prime(n: int) -> bool:
    """Check if a number is prime."""
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True
