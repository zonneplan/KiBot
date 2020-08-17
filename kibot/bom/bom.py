# -*- coding: utf-8 -*-
# Copyright (c) 2020 Salvador E. Tropea
# Copyright (c) 2020 Instituto Nacional de Tecnología Industrial
# Copyright (c) 2016-2020 Oliver Henry Walters (@SchrodingersGat)
# License: MIT
# Project: KiBot (formerly KiPlot)
# Adapted from: https://github.com/SchrodingersGat/KiBoM
# Contributors: Kenny Huynh (@hkennyv)
"""
All the logic to convert a list of components into the rows and columns used to create the BoM.
"""
import locale
from copy import deepcopy
from .units import compare_values, comp_match
from .bom_writer import write_bom
from .columnlist import ColumnList
from .. import log

logger = log.get_logger(__name__)
# Supported values for "do not fit"
DNF = {
    "dnf": 1,
    "dnl": 1,
    "dnp": 1,
    "do not fit": 1,
    "do not place": 1,
    "do not load": 1,
    "nofit": 1,
    "nostuff": 1,
    "noplace": 1,
    "noload": 1,
    "not fitted": 1,
    "not loaded": 1,
    "not placed": 1,
    "no stuff": 1,
}
# String matches for marking a component as "do not change" or "fixed"
DNC = {
    "dnc": 1,
    "do not change": 1,
    "no change": 1,
    "fixed": 1
}
# RV == Resistor Variable or Varistor
# RN == Resistor 'N'(Pack)
# RT == Thermistor
RLC_PREFIX = {'R': 1, 'L': 1, 'C': 1, 'RV': 1, 'RN': 1, 'RT': 1}


def compare_value(c1, c2, cfg):
    """ Compare the value of two components """
    # Simple string comparison
    if c1.value.lower() == c2.value.lower():
        return True
    # Otherwise, perform a more complicated value comparison
    if compare_values(c1, c2):
        return True
    # Ignore value if both components are connectors
    # Note: Is common practice to use the "Value" field of connectors to denote its use.
    #       In this case the values won't match even when the connectors are equivalent.
    if cfg.group_connectors:
        if 'connector' in c1.lib.lower() and 'connector' in c2.lib.lower():
            return True
    # No match, return False
    return False


def compare_part_name(c1, c2, cfg):
    """ Determine if two parts have the same name, compute aliases """
    pn1 = c1.name.lower()
    pn2 = c2.name.lower()
    # Simple direct match
    if pn1 == pn2:
        return True
    # Compare part aliases e.g. "c" to "c_small"
    for alias in cfg.component_aliases:
        if pn1 in alias and pn2 in alias:
            return True
    return False


def compare_field(c1, c2, field, cfg):
    c1_field = c1.get_field_value(field).lower()
    c2_field = c2.get_field_value(field).lower()
    # If blank comparisons are allowed
    if (c1_field == "" or c2_field == "") and cfg.merge_blank_fields:
        return True
    return c1_field == c2_field


def compare_components(c1, c2, cfg):
    """ Determine if two parts are 'equal' """
    # 'fitted' value must be the same for both parts
    if c1.fitted != c2.fitted:
        return False
    # 'fixed' value must be the same for both parts
    if c1.fixed != c2.fixed:
        return False
    # Do not group components
    if len(cfg.group_fields) == 0:
        return c1.ref == c2.ref
    # Check if the grouping fields match
    for c in cfg.group_fields:
        # Perform special matches
        if c == ColumnList.COL_VALUE_L:
            if not compare_value(c1, c2, cfg):
                return False
        # Match part name
        elif c == ColumnList.COL_PART_L:
            if not compare_part_name(c1, c2, cfg):
                return False
        # Generic match
        elif not compare_field(c1, c2, c, cfg):
            return False
    return True


class Joiner:
    def __init__(self):
        self.stack = []

    def add(self, P, N):
        if not self.stack:
            self.stack.append(((P, N), (P, N)))
            return
        S, E = self.stack[-1]
        if N == E[1] + 1:
            self.stack[-1] = (S, (P, N))
        else:
            self.stack.append(((P, N), (P, N)))

    def flush(self, sep, dash='-'):
        refstr = u''
        c = 0
        for Q in self.stack:
            if c != 0:
                refstr += sep
            S, E = Q
            if S == E:
                refstr += "%s%d" % S
                c += 1
            else:
                # Do we have space?
                refstr += "%s%d%s%s%d" % (S[0], S[1], dash, E[0], E[1])
                c += 2
        return refstr


def _suffix_to_num(suffix):
    return 0 if suffix == '?' else int(suffix)


class ComponentGroup(object):
    """ A row in the BoM """
    def __init__(self, cfg):
        """ Initialize the group with no components, and default fields """
        self.components = []
        self.refs = {}
        self.cfg = cfg
        # Columns loaded from KiCad
        self.fields = {c.lower(): None for c in ColumnList.COLUMNS_DEFAULT}
        self.field_names = deepcopy(ColumnList.COLUMNS_DEFAULT)

    def match_component(self, c):
        """ Test if a given component fits in this group """
        return compare_components(c, self.components[0], self.cfg)

    def contains_component(self, c):
        """ Test if a given component is already contained in this group """
        return c.ref in self.refs

    def add_component(self, c):
        """ Add a component to the group.
            Avoid repetition, checks if suitable.
            Note: repeated components happend when a component contains more than one unit """
        if not self.components:
            self.components.append(c)
            self.refs[c.ref] = c
        elif self.contains_component(c):
            return
        elif self.match_component(c):
            self.components.append(c)
            self.refs[c.ref] = c

    def get_count(self):
        return len(self.components)

    def is_fitted(self):
        # compare_components ensures all has the same status
        return self.components[0].fitted

    def is_fixed(self):
        # compare_components ensures all has the same status
        return self.components[0].fixed

    def get_field(self, field):
        field = field.lower()
        if field not in self.fields or not self.fields[field]:
            return ""
        return self.fields[field]

    def sort_components(self):
        """ Sort the components in correct order (by reference).
            First priority is the prefix, second the number (as integer) """
        self.components = sorted(self.components, key=lambda c: [c.ref_prefix, _suffix_to_num(c.ref_suffix)])

    def get_refs(self):
        """ Return a list of the components """
        return " ".join([c.ref for c in self.components])

    def get_alt_refs(self):
        """ Alternative list of references using ranges """
        S = Joiner()
        for n in self.components:
            P, N = (n.ref_prefix, _suffix_to_num(n.ref_suffix))
            S.add(P, N)
        return S.flush(' ')

    def update_field(self, field, value, ref=None):
        """ Update a given field, concatenates existing values and informs a collision """
        if not value:
            return
        field_ori = field
        field = field.lower()
        if (field not in self.fields) or (not self.fields[field]):
            self.fields[field] = value
            self.field_names.append(field_ori)
        elif value.lower() in self.fields[field].lower():
            return
        else:
            # Config contains variant information, which is different for each component
            # Part can be one of the defined aliases
            if field != self.cfg.fit_field and field != 'part':
                logger.warning("Field conflict: ({refs}) [{name}] : '{flds}' <- '{fld}' (in {ref})".format(
                    refs=self.get_refs(),
                    name=field,
                    flds=self.fields[field],
                    fld=value, ref=ref))
            self.fields[field] += " " + value

    def update_fields(self, usealt=False):
        for c in self.components:
            for f, v in c.get_user_fields():
                self.update_field(f, v, c.ref)
        # Update 'global' fields
        if usealt:
            self.fields[ColumnList.COL_REFERENCE_L] = self.get_alt_refs()
        else:
            self.fields[ColumnList.COL_REFERENCE_L] = self.get_refs()
        # Quantity
        q = self.get_count()
        self.fields[ColumnList.COL_GRP_QUANTITY_L] = "{n}{dnf}{dnc}".format(
            n=q,
            dnf=" (DNF)" if not self.is_fitted() else "",
            dnc=" (DNC)" if self.is_fixed() else "")

        self.fields[ColumnList.COL_GRP_BUILD_QUANTITY_L] = str(q * self.cfg.number) if self.is_fitted() else "0"
        comp = self.components[0]
        self.fields[ColumnList.COL_VALUE_L] = comp.value
        self.fields[ColumnList.COL_PART_L] = comp.name
        self.fields[ColumnList.COL_PART_LIB_L] = comp.lib
        self.fields[ColumnList.COL_DATASHEET_L] = comp.datasheet
        self.fields[ColumnList.COL_FP_L] = comp.footprint
        self.fields[ColumnList.COL_FP_LIB_L] = comp.footprint_lib
        self.fields[ColumnList.COL_SHEETPATH_L] = comp.sheet_path_h
        if not self.fields[ColumnList.COL_DESCRIPTION_L]:
            self.fields[ColumnList.COL_DESCRIPTION_L] = comp.desc

    def get_row(self, columns):
        """ Return a dict of the KiCad data based on the supplied columns """
        row = []
        for key in columns:
            val = self.get_field(key)
            # Join fields (appending to current value)
            for join_l in self.cfg.join:
                # Each list is "target, source..." so we need at least 2 elements
                elements = len(join_l)
                target = join_l[0]
                if elements > 1 and target == key:
                    # Append data from the other fields
                    for source in join_l[1:]:
                        v = self.get_field(source)
                        if v:
                            val = val + ' ' + v
            row.append(val)
        return row


def test_reg_exclude(cfg, c):
    """ Test if this part should be included, based on any regex expressions provided in the preferences """
    for reg in cfg.exclude_any:
        field_value = c.get_field_value(reg.column)
        if reg.regex.search(field_value):
            if cfg.debug_level > 1:
                logger.debug("Excluding '{ref}': Field '{field}' ({value}) matched '{re}'".format(
                             ref=c.ref, field=reg.column, value=field_value, re=reg.regex))
            # Found a match
            return True
    # Default, could not find any matches
    return False


def test_reg_include(cfg, c):
    """ Reject components that doesn't match the provided regex.
        So we include only the components that matches any of the regexs. """
    if not cfg.include_only:  # Nothing to match against, means include all
        return True
    for reg in cfg.include_only:
        field_value = c.get_field_value(reg.column)
        if reg.regex.search(field_value):
            if cfg.debug_level > 1:
                logger.debug("Including '{ref}': Field '{field}' ({value}) matched '{re}'".format(
                             ref=c.ref, field=reg.column, value=field_value, re=reg.regex))
                # Found a match
                return True
    # Default, could not find a match
    return False


def get_value_sort(comp):
    """ Try to better sort R, L and C components """
    res = comp.value_sort
    if res:
        value, (mult, mult_s), unit = res
        if comp.ref_prefix in "CL":
            # fempto Farads
            value = "{0:15d}".format(int(value * 1e15 * mult + 0.1))
        else:
            # milli Ohms
            value = "{0:15d}".format(int(value * 1000 * mult + 0.1))
        return value
    return comp.value


def normalize_value(c, decimal_point):
    if c.value_sort is None:
        return c.value
    value, (mult, mult_s), unit = c.value_sort
    ivalue = int(value)
    if value == ivalue:
        value = ivalue
    elif decimal_point:
        value = str(value).replace('.', decimal_point)
    return '{} {}{}'.format(value, mult_s, unit)


def group_components(cfg, components):
    groups = []
    # Iterate through each component, and test whether a group for these already exists
    for c in components:
        if cfg.test_regex:
            # Skip components if they do not meet regex requirements
            if not test_reg_include(cfg, c):
                continue
            if test_reg_exclude(cfg, c):
                continue
        # Cache the value used to sort
        if c.ref_prefix in RLC_PREFIX:
            c.value_sort = comp_match(c.value, c.ref_prefix)
        else:
            c.value_sort = None
        # Try to add the component to an existing group
        found = False
        for g in groups:
            if g.match_component(c):
                g.add_component(c)
                found = True
                break
        if not found:
            # Create a new group
            g = ComponentGroup(cfg)
            g.add_component(c)
            groups.append(g)
    # Now unify the data from the components of each group
    decimal_point = None
    if cfg.normalize_locale:
        decimal_point = locale.localeconv()['decimal_point']
        if decimal_point == '.':
            decimal_point = None
    for g in groups:
        # Sort the references within each group
        g.sort_components()
        # Fill the columns
        g.update_fields(cfg.use_alt)
        if cfg.normalize_values:
            g.fields[ColumnList.COL_VALUE_L] = normalize_value(g.components[0], decimal_point)
    # Sort the groups
    # First priority is the Type of component (e.g. R?, U?, L?)
    groups = sorted(groups, key=lambda g: [g.components[0].ref_prefix, get_value_sort(g.components[0])])
    # Enumerate the groups and compute stats
    n_total = 0
    n_fitted = 0
    c = 1
    dnf = 1
    cfg.n_groups = len(groups)
    for g in groups:
        is_fitted = g.is_fitted()
        if cfg.ignore_dnf and not is_fitted:
            g.update_field('Row', str(dnf))
            dnf += 1
        else:
            g.update_field('Row', str(c))
            c += 1
        # Stats
        g_l = g.get_count()
        n_total += g_l
        if is_fitted:
            n_fitted += g_l
    cfg.n_total = n_total
    cfg.n_fitted = n_fitted
    cfg.n_build = n_fitted * cfg.number
    return groups


def comp_is_fixed(value, config, variants):
    """ Determine if a component is FIXED or not.
        Fixed components shouldn't be replaced without express authorization.
        value: component value (lowercase).
        config: content of the 'Config' field (lowercase).
        variants: list of variants to match. """
    # Check the value field first
    if value in DNC:
        return True
    # Empty is not fixed
    if not config:
        return False
    # Also support space separated list (simple cases)
    opts = config.split(" ")
    for opt in opts:
        if opt in DNC:
            return True
    # Normal separator is ","
    opts = config.split(",")
    for opt in opts:
        if opt in DNC:
            return True
    return False


def comp_is_fitted(value, config, variants):
    """ Determine if a component will be or not.
        value: component value (lowercase).
        config: content of the 'Config' field (lowercase).
        variants: list of variants to match. """
    # Check the value field first
    if value in DNF:
        return False
    # Empty value means part is fitted
    if not config:
        return True
    # Also support space separated list (simple cases)
    opts = config.split(" ")
    for opt in opts:
        if opt in DNF:
            return False
    # Variants logic
    opts = config.split(",")
    for opt in opts:
        opt = opt.strip()
        # Any option containing a DNF is not fitted
        if opt in DNF:
            return False
        # Options that start with '-' are explicitly removed from certain configurations
        if opt.startswith("-") and opt[1:] in variants:
            return False
        # Options that start with '+' are fitted only for certain configurations
        if opt.startswith("+") and opt[1:] not in variants:
            return False
    return True


def do_bom(file_name, ext, comps, cfg):
    # Make the config field name lowercase
    cfg.fit_field = cfg.fit_field.lower()
    f_config = cfg.fit_field
    # Make the variants lowercase
    variants = [v.lower() for v in cfg.variant]
    # Solve `fixed` and `fitted` attributes for all components
    for c in comps:
        value = c.value.lower()
        config = c.get_field_value(f_config).lower()
        c.fitted = comp_is_fitted(value, config, variants)
        if cfg.debug_level > 2:
            logger.debug('ref: {} value: {} config: {} variants: {} -> fitted {}'.
                         format(c.ref, value, config, variants, c.fitted))
        c.fixed = comp_is_fixed(value, config, variants)
    # Group components according to group_fields
    groups = group_components(cfg, comps)
    # Give a name to empty variant
    if not variants:
        cfg.variant = ['default']
    # Create the BoM
    logger.debug("Saving BOM File: "+file_name)
    write_bom(file_name, ext, groups, cfg.columns, cfg)
