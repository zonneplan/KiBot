# Classes to edit the different data types used for the YAML config
# Each class should provide a suitable widget

import math
import wx
from .validators import NumberValidator
from .. import log
logger = log.get_logger()
TYPE_PRIORITY = {'list(dict)': 100, 'list(list(string))': 90, 'list(string)': 80, 'dict': 60, 'string': 50, 'number': 20,
                 'boolean': 10}
max_label = 200
def_text = 200


class DataTypeBase(object):
    def __init__(self, kind, restriction, default):
        self.kind = kind
        self.restriction = restriction
        self.default = default
        self.is_dict = kind == 'dict' or kind == 'list(dist)'

    def get_widget(self, obj, parent, entry, level):
        return None

    def get_restriction_help(self):
        return ''

    def get_label(self, entry):
        return entry.name

    def get_value(self):
        return None


class DataTypeString(DataTypeBase):
    def get_widget(self, obj, parent, entry, level):
        help = entry.help
        help += self.get_restriction_help()
        if self.default is not None:
            help += f'\nDefault: {self.default}'
        e_sizer = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(parent, label=self.get_label(entry), size=wx.Size(max_label, -1), style=wx.ALIGN_RIGHT)
        label.SetToolTip(help)
        self.input = wx.TextCtrl(parent, value=str(getattr(obj, entry.name)), size=wx.Size(def_text, -1))
        self.input.SetToolTip(help)
        e_sizer.Add(label, 0, wx.EXPAND | wx.ALL, 5)
        e_sizer.Add(self.input, 1, wx.EXPAND | wx.ALL, 5)
        return e_sizer

    def get_value(self):
        return self.input.Value


class DataTypeNumber(DataTypeString):
    def __init__(self, kind, restriction, default):
        super().__init__(kind, restriction, default)
        if restriction is None:
            restriction = (-math.inf, math.inf)
        else:
            if restriction[0] is None:
                restriction[0] = -math.inf
            if restriction[1] is None:
                restriction[1] = math.inf
        self.restriction = restriction

    def get_widget(self, obj, parent, entry, level):
        sizer = super().get_widget(obj, parent, entry, level)
        self.input.SetValidator(NumberValidator(self.input, self.restriction, self.default))
        return sizer

    def get_label(self, entry):
        return entry.name + f' [{self.restriction[0]},{self.restriction[1]}]'

    def get_restriction_help(self):
        return f'\nRange: {self.restriction[0]} to {self.restriction[1]}'

    def get_value(self):
        val = self.input.Value
        if val == '-' or val == '':
            return self.default
        return float(val)


class DataTypeBoolean(DataTypeBase):
    def get_widget(self, obj, parent, entry, level):
        help = entry.help
        if self.default is not None:
            help += f'\nDefault: {self.default}'
        e_sizer = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(parent, label=self.get_label(entry), size=wx.Size(max_label, -1), style=wx.ALIGN_RIGHT)
        label.SetToolTip(help)
        self.input = wx.CheckBox(parent)
        self.input.SetValue(getattr(obj, entry.name))
        self.input.SetToolTip(help)
        e_sizer.Add(label, 0, wx.EXPAND | wx.ALL, 5)
        e_sizer.Add(self.input, 1, wx.EXPAND | wx.ALL, 5)
        return e_sizer

    def get_value(self):
        return self.input.GetValue()


class DataTypeChoice(DataTypeBase):
    def get_widget(self, obj, parent, entry, level):
        help = entry.help
        if self.default is not None:
            help += f'\nDefault: {self.default}'
        e_sizer = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(parent, label=self.get_label(entry), size=wx.Size(max_label, -1), style=wx.ALIGN_RIGHT)
        label.SetToolTip(help)
        self.input = wx.Choice(parent, choices=self.restriction)
        val = getattr(obj, entry.name)
        self.input.SetSelection(self.restriction.index(val))
        self.input.SetToolTip(help)
        e_sizer.Add(label, 0, wx.EXPAND | wx.ALL, 5)
        e_sizer.Add(self.input, 1, wx.EXPAND | wx.ALL, 5)
        return e_sizer

    def get_value(self):
        return self.restriction[self.input.GetSelection()]


class DataTypeDict(DataTypeBase):
    def get_widget(self, obj, parent, entry, level):

        help = entry.help
        e_sizer = wx.BoxSizer(wx.HORIZONTAL)
        cp = wx.CollapsiblePane(parent, label=self.get_label(entry))
        cp.SetToolTip(help)
        # cp.Collapse(False)  # Start expanded

        pane = cp.GetPane()
        pane_sizer = wx.BoxSizer(wx.VERTICAL)
        sub_obj = getattr(obj, entry.name)
        add_widgets(sub_obj, entry.sub, pane, pane_sizer, level+1)
        pane.SetSizer(pane_sizer)

        e_sizer.Add(cp, 1, wx.EXPAND | wx.ALL, 5)
        return e_sizer


# ##################################################################################################
#  End of DataType* classes
# ##################################################################################################


def get_class_for(kind, rest):
    """ Return a class suitable to edit data of the *kind* type. """
    if kind == 'string':
        if rest is not None:
            return DataTypeChoice
        return DataTypeString
    elif kind == 'number':
        return DataTypeNumber
    elif kind == 'boolean':
        return DataTypeBoolean
    elif kind == 'dict':
        return DataTypeDict
    return DataTypeBase


def add_widgets(obj, entries, parent, sizer, level=0):
    if isinstance(obj, type):
        logger.error(f'- !!! {obj.__dict__} {type(obj)}')
        return

    # Compute the len for the largest label
    font = wx.StaticText(parent).GetFont()
    dc = wx.ScreenDC()
    dc.SetFont(font)
    global max_label
    cur_max = max_label
    max_label = max((dc.GetTextExtent(e.name).width for e in entries))
    # Size for input boxes
    global def_text
    def_text = dc.GetTextExtent('M'*40).width

    for entry in entries:
        if entry.name == 'type':
            continue
        logger.info(f'{entry.name} {entry.valids[0].kind}')
        e_sizer = entry.valids[0].get_widget(obj, parent, entry, level)
        if e_sizer:
            sizer.Add(e_sizer, 0, wx.EXPAND | wx.ALL, 0)
        else:
            logger.error(f'{entry.name} {entry.valids[0].kind}')
    max_label = cur_max


class DataEntry(object):
    """ Class to represent one data to be edited """
    def __init__(self, name, valids, def_val, help):
        self.name = name
        self.valids = valids
        self.def_val = def_val
        self.help = '\n'.join((ln.strip() for ln in help.splitlines(True)))
        self.is_dict = any((x.is_dict for x in valids))


def get_data_type_tree(obj):
    """ Create a tree containing all the DataEntry objects associated to the data in the *obj* output """
    entries = []
    for k, v in obj.get_attrs_for().items():
        if k[0] == '_':
            continue
        help, _, is_alias = obj.get_doc(k, no_basic=True)
        if help is None or is_alias:
            continue
        case = f'{k} = `{v}`'
        assert help[0] == '[', case
        valid, extra, def_val, real_help = obj.get_valid_types(help)
        valids = [get_class_for(v, e)(v, e, def_val) for v, e in zip(valid, extra)]
        case += f' {extra} """ {help} """'
        assert valids, case
        valids = sorted(valids, key=lambda x: 200-TYPE_PRIORITY[x.kind])
        entry = DataEntry(k, valids, def_val, real_help)
        if entry.is_dict:
            entry.sub = get_data_type_tree(v)
        entries.append(entry)
    return entries
