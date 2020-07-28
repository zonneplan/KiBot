"""
ColumnList
This code is adapted from https://github.com/SchrodingersGat/KiBoM by Oliver Henry Walters.

This is a class to hold the names of the fields and columns of the BoM.
"""


class ColumnList:
    """ A list of columns for the BoM """
    # Default columns (immutable)
    # TODO: KiBoM uses Reference*s*, good for a column, bad for a field name.
    COL_REFERENCE = 'Reference'
    COL_REFERENCE_L = COL_REFERENCE.lower()
    COL_DESCRIPTION = 'Description'
    COL_DESCRIPTION_L = COL_DESCRIPTION.lower()
    COL_VALUE = 'Value'
    COL_VALUE_L = COL_VALUE.lower()
    COL_FP = 'Footprint'
    COL_FP_L = COL_FP.lower()
    COL_FP_LIB = 'Footprint Lib'
    COL_FP_LIB_L = COL_FP_LIB.lower()
    COL_PART = 'Part'
    COL_PART_L = COL_PART.lower()
    COL_PART_LIB = 'Part Lib'
    COL_PART_LIB_L = COL_PART_LIB.lower()
    COL_DATASHEET = 'Datasheet'
    COL_DATASHEET_L = COL_DATASHEET.lower()

    # Default columns for groups
    COL_GRP_QUANTITY = 'Quantity Per PCB'
    COL_GRP_QUANTITY_L = COL_GRP_QUANTITY.lower()
    # COL_GRP_TOTAL_COST = 'Total Cost'
    # COL_GRP_TOTAL_COST_L = COL_GRP_TOTAL_COST.lower()
    COL_GRP_BUILD_QUANTITY = 'Build Quantity'
    COL_GRP_BUILD_QUANTITY_L = COL_GRP_BUILD_QUANTITY.lower()

    # Generated columns
    COLUMNS_GEN_L = [
        COL_GRP_QUANTITY_L,
        COL_GRP_BUILD_QUANTITY_L,
    ]

    # Default columns
    COLUMNS_DEFAULT = [
        COL_DESCRIPTION,
        COL_PART,
        COL_PART_LIB,
        COL_REFERENCE,
        COL_VALUE,
        COL_FP,
        COL_FP_LIB,
        COL_GRP_QUANTITY,
        COL_GRP_BUILD_QUANTITY,
        COL_DATASHEET
    ]

    # Default columns
    # These columns are 'immutable'
    COLUMNS_PROTECTED_L = {
        COL_REFERENCE_L: 1,
        COL_GRP_QUANTITY_L: 1,
        COL_VALUE_L: 1,
        COL_PART_L: 1,
        COL_PART_LIB_L: 1,
        COL_DESCRIPTION_L: 1,
        COL_DATASHEET_L: 1,
        COL_FP_L: 1,
        COL_FP_LIB_L: 1
    }

    # Default fields used to group components
    DEFAULT_GROUPING = [
        COL_PART_L,
        COL_PART_LIB_L,
        COL_VALUE_L,
        COL_FP_L,
        COL_FP_LIB_L,
    ]

    def __init__(self, cols=None):
        self.columns = []
        self.columns_l = {}
        if not cols:
            cols = ColumnList.COLUMNS_DEFAULT
        # Make a copy of the supplied columns
        for col in cols:
            self.add_column(col)

    def _has_column(self, col):
        return col.lower() in self.columns_l

    def add_column(self, col):
        """ Add a new column (if it doesn't already exist!) """
        # Already exists?
        if self._has_column(col):
            return
        # To enable fast lowercase search
        self.columns_l[col.lower()] = col
        # Case sensitive version
        self.columns.append(col)

    def remove_column(self, col):
        """ Remove a column from the list. Specify either the heading or the index """
        if type(col) is str:
            self.remove_column_by_name(col)
        elif type(col) is int and col >= 0 and col < len(self.columns):
            self.remove_column_by_name(self.columns[col])

    def remove_column_by_name(self, name):
        name = name.lower()
        # First check if this is in an immutable colum
        if name in self.COLUMNS_PROTECTED_L:
            return
        # Column does not exist, return
        if name not in self.columns_l:
            return
        name = self.columns_l[name]
        index = self.columns.index(name)
        del self.columns[index]
