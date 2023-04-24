# Author: Salvador E. Tropea
# License: MIT
from ..bom.units import comp_match


def read_resistance(value: str):
    """
    Given a string, try to parse resistance and return it as Ohms (Decimal)

    This function can raise a ValueError if the value is invalid
    """
    res = comp_match(value, 'R')
    if res is None:
        raise ValueError(f"Cannot parse '{value}' to resistance")
    return res.get_decimal(), res.get_extra('tolerance')
