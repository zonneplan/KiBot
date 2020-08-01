from re import compile, IGNORECASE
from .gs import GS
from .optionable import Optionable, BaseOptions
from .error import KiPlotConfigurationError
from kiplot.macros import macros, document, output_class  # noqa: F401
from .bom.columnlist import ColumnList
from .bom.bom import do_bom
from . import log

logger = log.get_logger(__name__)


# String matches for marking a component as "do not fit"
class BoMRegex(Optionable):
    """ Implements the pair column/regex """
    def __init__(self):
        super().__init__()
        self._unkown_is_error = True
        with document:
            self.column = ''
            """ Name of the column to apply the regular expression """
            self.regex = ''
            """ Regular expression to match """
            self.field = None
            """ {column} """
            self.regexp = None
            """ {regex} """  # pragma: no cover

    def __str__(self):
        # TODO make a list
        return self.column+'\t'+self.regex


class BoMColumns(Optionable):
    """ Information for the BoM columns """
    def __init__(self):
        super().__init__()
        self._unkown_is_error = True
        with document:
            self.field = ''
            """ Name of the field to use for this column """
            self.name = ''
            """ Name to display in the header. The field is used when empty """
            self.join = Optionable
            """ [list(string)|string] List of fields to join to this column """  # pragma: no cover

    def config(self):
        super().config()
        if not self.field:
            raise KiPlotConfigurationError("Missing or empty `field` in columns list ({})".format(str(self._tree)))
        # Ensure this is None or a list
        if isinstance(self.join, type):
            self.join = None
        elif isinstance(self.join, str):
            self.join = [self.join]


class BoMOptions(BaseOptions):
    DEFAULT_ALIASES = [['r', 'r_small', 'res', 'resistor'],
                       ['l', 'l_small', 'inductor'],
                       ['c', 'c_small', 'cap', 'capacitor'],
                       ['sw', 'switch'],
                       ['zener', 'zenersmall'],
                       ['d', 'diode', 'd_small'],
                       ]
    DEFAULT_EXCLUDE = [[ColumnList.COL_REFERENCE, '^TP[0-9]*'],
                       [ColumnList.COL_REFERENCE, '^FID'],
                       [ColumnList.COL_PART, 'mount.*hole'],
                       [ColumnList.COL_PART, 'solder.*bridge'],
                       [ColumnList.COL_PART, 'test.*point'],
                       [ColumnList.COL_FP, 'test.*point'],
                       [ColumnList.COL_FP, 'mount.*hole'],
                       [ColumnList.COL_FP, 'fiducial'],
                       ]

    def __init__(self):
        with document:
            self.number = 1
            """ Number of boards to build (components multiplier) """
            self.variant = ''
            """ Board variant(s), used to determine which components
                are output to the BoM. """
            self.separator = ','
            """ CSV Separator """
            self.output = GS.def_global_output
            """ filename for the output (%i=bom)"""
            self.format = 'HTML'
            """ [HTML,CSV,TXT,TSV,XML,XLSX] format for the BoM """
            # Equivalent to KiBoM INI:
            self.ignore_dnf = True
            """ Exclude DNF (Do Not Fit) components """
            self.html_generate_dnf = True
            """ Generate a separated section for DNF (Do Not Fit) components (HTML only) """
            self.use_alt = False
            """ Print grouped references in the alternate compressed style eg: R1-R7,R18 """
            self.group_connectors = True
            """ Connectors with the same footprints will be grouped together, independent of the name of the connector """
            self.test_regex = True
            """ Each component group will be tested against a number of regular-expressions (see ``). """
            self.merge_blank_fields = True
            """ Component groups with blank fields will be merged into the most compatible group, where possible """
            self.fit_field = 'Config'
            """ Field name used to determine if a particular part is to be fitted (also DNC and variants) """
            self.datasheet_as_link = ''
            """ Column with links to the datasheet (HTML only) """
            self.hide_headers = False
            """ Hide column headers """
            self.hide_pcb_info = False
            """ Hide project information """
            self.digikey_link = Optionable
            """ [string|list(string)] Column/s containing Digi-Key part numbers, will be linked to web page (HTML only) """
            self.group_fields = Optionable
            """ [list(string)] List of fields used for sorting individual components into groups.
                Components which match (comparing *all* fields) will be grouped together.
                Field names are case-insensitive.
                If empty: ['Part', 'Part Lib', 'Value', 'Footprint', 'Footprint Lib'] is used """
            self.component_aliases = Optionable
            """ [list(list(string))] A series of values which are considered to be equivalent for the part name.
                Each entry is a list of equivalen names. Example: ['c', 'c_small', 'cap' ]
                will ensure the equivalent capacitor symbols can be grouped together.
                If empty the following aliases are used:
                - ['r', 'r_small', 'res', 'resistor']
                - ['l', 'l_small', 'inductor']
                - ['c', 'c_small', 'cap', 'capacitor']
                - ['sw', 'switch']
                - ['zener', 'zenersmall']
                - ['d', 'diode', 'd_small'] """
            self.include_only = BoMRegex
            """ [list(dict)] A series of regular expressions used to select included parts.
                If there are any regex defined here, only components that match against ANY of them will be included.
                Column names are case-insensitive.
                If empty all the components are included """
            self.exclude_any = BoMRegex
            """ [list(dict)] A series of regular expressions used to exclude parts.
                If a component matches ANY of these, it will be excluded.
                Column names are case-insensitive.
                If empty the following list is used:
                - column: References
                ..regex: '^TP[0-9]*'
                - column: References
                ..regex: '^FID'
                - column: Part
                ..regex: 'mount.*hole'
                - column: Part
                ..regex: 'solder.*bridge'
                - column: Part
                ..regex: 'test.*point'
                - column: Footprint
                ..regex 'test.*point'
                - column: Footprint
                ..regex: 'mount.*hole'
                - column: Footprint
                ..regex: 'fiducial' """
            self.columns = BoMColumns
            """ [list(dict)|list(string)] List of columns to display.
                Can be just the name of the field """  # pragma: no cover
        super().__init__()

    @staticmethod
    def _get_columns():
        """ Create a list of valid columns """
        if GS.sch:
            return GS.sch.get_field_names(ColumnList.COLUMNS_DEFAULT)

    def config(self):
        super().config()
        # digikey_link
        if isinstance(self.digikey_link, type):
            self.digikey_link = None
        elif isinstance(self.digikey_link, list):
            self.digikey_link = '\t'.join(self.digikey_link)
        # group_fields
        if isinstance(self.group_fields, type):
            self.group_fields = ColumnList.DEFAULT_GROUPING
        else:
            # Make the grouping fields lowercase
            self.group_fields = [f.lower() for f in self.group_fields]
        # component_aliases
        if isinstance(self.component_aliases, type):
            self.component_aliases = BoMOptions.DEFAULT_ALIASES
        # include_only
        if isinstance(self.include_only, type):
            self.include_only = None
        else:
            for r in self.include_only:
                r.regex = compile(r.regex, flags=IGNORECASE)
        # exclude_any
        if isinstance(self.exclude_any, type):
            self.exclude_any = []
            for r in BoMOptions.DEFAULT_EXCLUDE:
                o = BoMRegex()
                o.column = r[0]
                o.regex = compile(r[1], flags=IGNORECASE)
                self.exclude_any.append(o)
        else:
            for r in self.exclude_any:
                r.regex = compile(r.regex, flags=IGNORECASE)
        # columns
        self.column_rename = {}
        self.join = []
        if isinstance(self.columns, type):
            self.columns = None
            # Ignore the library part and footprint
            self.ignore = [ColumnList.COL_PART_LIB_L, ColumnList.COL_FP_LIB_L, ColumnList.COL_SHEETPATH_L]
        else:
            # This is tricky
            # Lower case available columns
            valid_columns = self._get_columns()
            valid_columns.append(ColumnList.COL_ROW_NUMBER)
            valid_columns_l = {c.lower(): c for c in valid_columns}
            logger.debug("Valid columns: "+str(valid_columns))
            # Create the different lists
            columns = []
            columns_l = {}
            for col in self.columns:
                if isinstance(col, str):
                    # Just a string, add to the list of used
                    new_col = col
                else:
                    # A complete entry
                    new_col = col.field
                    # A column rename
                    if col.name:
                        self.column_rename[col.field.lower()] = col.name
                    # Attach other columns
                    if col.join:
                        self.join.append([col.field]+col.join)
                # Check this is a valid column
                if new_col.lower() not in valid_columns_l:
                    raise KiPlotConfigurationError('Invalid column name `{}`'.format(new_col))
                columns.append(new_col)
                columns_l[new_col.lower()] = new_col
            # Create a list of the columns we don't want
            self.ignore = [c for c in valid_columns_l.keys() if c not in columns_l]
            # And this is the ordered list with the case style defined by the user
            self.columns = columns

    def run(self, output_dir, board):
        format = self.format.lower()
        output = self.expand_filename_sch(output_dir, self.output, 'bom', format)
        self.variant = self.variant.split(',')
        # Add some info needed for the output to the config object.
        # So all the configuration is contained in one object.
        self.source = GS.sch_basename
        self.date = GS.sch_date
        self.revision = GS.sch_rev
        self.debug_level = GS.debug_level
        # Get the components list from the schematic
        comps = GS.sch.get_components()
        do_bom(output, format, comps, self)


@output_class
class BoM(BaseOutput):  # noqa: F821
    """ BoM (Bill of Materials)
        Used to generate the BoM in CSV, HTML, TSV, TXT, XML or XLSX format using the internal BoM.
        Is compatible with KiBoM, but doesn't need to update the XML netlist because the components
        are loaded from the schematic.
        Important differences with KiBoM output:
        - All options are in the main `options` section, not in `conf` subsection.
        - The `Component` column is named `Row` and works just like any other column.
        This output is what you get from the 'Tools/Generate Bill of Materials' menu in eeschema. """
    def __init__(self):
        super().__init__()
        with document:
            self.options = BoMOptions
            """ [dict] Options for the `bom` output """  # pragma: no cover
        self._sch_related = True
