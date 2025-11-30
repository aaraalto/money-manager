import math
from typing import List, Tuple

def calculate_mean(values: List[float]) -> float:
    """
    Calculates the arithmetic mean of a list of numbers.
    
    Args:
        values: List of numerical values.
        
    Returns:
        The mean value. Returns 0 if list is empty.
    """
    if not values:
        return 0.0
    return sum(values) / len(values)

def calculate_std_dev(values: List[float], is_sample: bool = True) -> float:
    """
    Calculates the standard deviation of a list of numbers.
    
    Args:
        values: List of numerical values.
        is_sample: If True (default), calculates sample standard deviation (N-1).
                   If False, calculates population standard deviation (N).
        
    Returns:
        The standard deviation. Returns 0 if list has fewer than 2 elements (for sample).
    """
    n = len(values)
    if n < 2 and is_sample:
        return 0.0
    if n == 0:
        return 0.0
        
    mean = calculate_mean(values)
    variance = sum((x - mean) ** 2 for x in values)
    
    divisor = n - 1 if is_sample else n
    if divisor == 0:
        return 0.0
        
    return math.sqrt(variance / divisor)

def calculate_linear_regression(x: List[float], y: List[float]) -> Tuple[float, float]:
    """
    Calculates the simple linear regression line (y = mx + b) for two sets of data.
    
    Args:
        x: Independent variable values.
        y: Dependent variable values.
        
    Returns:
        A tuple (slope, intercept).
        Returns (0.0, 0.0) if input lists are empty or mismatched in length.
    """
    n = len(x)
    if n != len(y) or n == 0:
        return 0.0, 0.0
        
    sum_x = sum(x)
    sum_y = sum(y)
    sum_xy = sum(xi * yi for xi, yi in zip(x, y))
    sum_x_sq = sum(xi ** 2 for xi in x)
    
    denominator = n * sum_x_sq - sum_x ** 2
    
    if denominator == 0:
        # Vertical line, undefined slope. Return 0 slope for safety.
        return 0.0, 0.0
        
    slope = (n * sum_xy - sum_x * sum_y) / denominator
    intercept = (sum_y - slope * sum_x) / n
    
    return slope, intercept

