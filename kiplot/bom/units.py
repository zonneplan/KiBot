# -*- coding: utf-8 -*-

"""
Units:
This code is adapted from https://github.com/SchrodingersGat/KiBoM by Oliver Henry Walters.

This file contains a set of functions for matching values which may be written in different formats
e.g.
0.1uF = 100n (different suffix specified, one has missing unit)
0R1 = 0.1Ohm (Unit replaces decimal, different units)

"""
import re
import locale

PREFIX_MICRO = [u"μ", "u", "micro"]
PREFIX_MILLI = ["milli", "m"]
PREFIX_NANO = ["nano", "n"]
PREFIX_PICO = ["pico", "p"]
PREFIX_KILO = ["kilo", "k"]
PREFIX_MEGA = ["mega", "meg", "M"]
PREFIX_GIGA = ["giga", "g"]

# All prefixes
PREFIX_ALL = PREFIX_PICO + PREFIX_NANO + PREFIX_MICRO + PREFIX_MILLI + PREFIX_KILO + PREFIX_MEGA + PREFIX_GIGA

# Common methods of expressing component units
UNIT_R = ["r", "ohms", "ohm", u"Ω"]
UNIT_C = ["farad", "f"]
UNIT_L = ["henry", "h"]

UNIT_ALL = UNIT_R + UNIT_C + UNIT_L

# Compiled regex to match the values
match = None
# Current locale decimal point value
decimal_point = None


def get_unit(unit):
    """
    Return a simplified version of a units string, for comparison purposes
    """

    if not unit:
        return None

    unit = unit.lower()

    if unit in UNIT_R:
        return "R"
    if unit in UNIT_C:
        return "F"
    if unit in UNIT_L:
        return "H"

    return None


def get_preffix(prefix):
    """
    Return the (numerical) value of a given prefix
    """

    if not prefix:
        return 1

    # 'M' is mega, 'm' is milli
    if prefix != 'M':
        prefix = prefix.lower()

    if prefix in PREFIX_PICO:
        return 1.0e-12
    if prefix in PREFIX_NANO:
        return 1.0e-9
    if prefix in PREFIX_MICRO:
        return 1.0e-6
    if prefix in PREFIX_MILLI:
        return 1.0e-3
    if prefix in PREFIX_KILO:
        return 1.0e3
    if prefix in PREFIX_MEGA:
        return 1.0e6
    if prefix in PREFIX_GIGA:
        return 1.0e9

    return 1


def group_string(group):  # Return a reg-ex string for a list of values
    return "|".join(group)


def match_string():
    return r"^([0-9\.]+)\s*(" + group_string(PREFIX_ALL) + ")*(" + group_string(UNIT_ALL) + r")*(\d*)$"


def comp_match(component):
    """
    Return a normalized value and units for a given component value string
    e.g. comp_match('10R2') returns (10, R)
    e.g. comp_match('3.3mOhm') returns (0.0033, R)
    """

    # Convert the decimal point from the current locale to a '.'
    global decimal_point
    if not decimal_point:
        decimal_point = locale.localeconv()['decimal_point']
    if decimal_point and decimal_point != '.':
        component = component.replace(decimal_point, ".")

    # Remove any commas
    component = component.strip().replace(",", "")

    # Get the compiled regex
    global match
    if not match:
        match = re.compile(match_string(), flags=re.IGNORECASE)

    # Not lower, but ignore case
    result = match.search(component)

    if not result:
        return None

    if not len(result.groups()) == 4:
        return None

    value, prefix, units, post = result.groups()

    # Special case where units is in the middle of the string
    # e.g. "0R05" for 0.05Ohm
    # In this case, we will NOT have a decimal
    # We will also have a trailing number

    if post and "." not in value:
        try:
            value = float(int(value))
            postValue = float(int(post)) / (10 ** len(post))
            value = value * 1.0 + postValue
        except ValueError:
            return None

    try:
        val = float(value)
    except ValueError:
        return None

    # Return all the data, let the caller join it
    return (val, get_preffix(prefix), get_unit(units))


def component_value(valString):

    result = comp_match(valString)

    if not result:
        return valString  # Return the same string back

    if not len(result) == 2:  # Result length is incorrect
        return valString

    val = result[0]

    return val


def compare_values(c1, c2):
    """ Compare two values """

    r1 = comp_match(c1)
    r2 = comp_match(c2)

    if not r1 or not r2:
        return False

    # Join the data to compare
    (v1, p1, u1) = r1
    (v2, p2, u2) = r2

    v1 = "{0:.15f}".format(v1 * 1.0 * p1)
    v2 = "{0:.15f}".format(v2 * 1.0 * p2)

    if v1 == v2:
        # Values match
        if u1 == u2:
            return True  # Units match
        if not u1:
            return True  # No units for component 1
        if not u2:
            return True  # No units for component 2

    return False
