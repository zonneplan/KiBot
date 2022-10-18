# Author: Salvador E. Tropea
# License: MIT
from decimal import Decimal
from ..bom.units import comp_match


def read_resistance(value: str) -> Decimal:
    """
    Given a string, try to parse resistance and return it as Ohms (Decimal)

    This function can raise a ValueError if the value is invalid
    """
    res = comp_match(value, 'R')
    if res is None:
        raise ValueError(f"Cannot parse '{value}' to resistance")
    v, mul, uni = res
    return Decimal(str(v))*Decimal(str(mul[0]))
