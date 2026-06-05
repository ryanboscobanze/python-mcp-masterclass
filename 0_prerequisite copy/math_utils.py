"""Support file for the modules section of 01_python_intermediate.ipynb.

Not a standalone lesson — used to demonstrate Python import patterns:
    from math_utils import circle_area
    from math_utils import PI
"""

PI = 3.14159

def circle_area(radius: float) -> float:
    return PI * radius ** 2