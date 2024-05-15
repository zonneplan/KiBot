# Classes to edit the different data types used for the YAML config
# Each class should provide a suitable widget

import math
import wx
from .validators import NumberValidator
from .gui_helpers import (get_btn_bitmap, move_sel_up, move_sel_down, ok_cancel, remove_item, input_label_and_text,
                          get_client_data, set_items, get_selection, get_emp_font)
from .gui_config import USE_DIALOG_FOR_NESTED
from ..registrable import RegOutput
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
        self.is_dict = kind == 'dict' or kind == 'list(dict)'

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
        self.input, sizer = input_label_and_text(parent, self.get_label(entry), str(getattr(obj, entry.name)), help,
                                                 def_text, max_label, entry.is_basic)
        return sizer

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
        if entry.is_basic:
            label.SetFont(get_emp_font())
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
        if entry.is_basic:
            label.SetFont(get_emp_font())
        label.SetToolTip(help)
        self.input = wx.Choice(parent, choices=self.restriction)
        val = getattr(obj, entry.name)
        try:
            self.input.SetSelection(self.restriction.index(val))
        except ValueError:
            # New entry
            self.input.SetSelection(0)
        self.input.SetToolTip(help)
        e_sizer.Add(label, 0, wx.EXPAND | wx.ALL, 5)
        e_sizer.Add(self.input, 1, wx.EXPAND | wx.ALL, 5)
        return e_sizer

    def get_value(self):
        return self.restriction[self.input.GetSelection()]


class DataTypeDict(DataTypeBase):
    def get_widget(self, obj, parent, entry, level):
        help = entry.help
        lbl = self.get_label(entry)
        self.sub_obj = getattr(obj, entry.name)
        self.parent = parent
        e_sizer = wx.BoxSizer(wx.HORIZONTAL)

        if USE_DIALOG_FOR_NESTED:
            self.entry_name = lbl
            self.btn = wx.Button(parent, label="Edit "+lbl)
            e_sizer.Add(self.btn, 1, wx.EXPAND | wx.ALL, 5)
            self.btn.Bind(wx.EVT_BUTTON, self.OnEdit)
            self.sub_entries = entry.sub
        else:
            # Collapsible pane version
            cp = wx.CollapsiblePane(parent, label=lbl)
            cp.SetToolTip(help)
            # cp.Collapse(False)  # Start expanded

            pane = cp.GetPane()
            pane_sizer = wx.BoxSizer(wx.VERTICAL)

            add_widgets(self.sub_obj, entry.sub, pane, pane_sizer, level+1)
            pane.SetSizer(pane_sizer)

            e_sizer.Add(cp, 1, wx.EXPAND | wx.ALL, 5)
        return e_sizer

    def OnEdit(self, event):
        edit_dict(self.parent.Parent, self.sub_obj, self.sub_entries, self.entry_name)


class InputStringDialog(wx.Dialog):
    def __init__(self, parent, lbl, title, help, initial=''):
        wx.Dialog.__init__(self, parent, title=title,
                           style=wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.input, inp_sizer = input_label_and_text(self, lbl, initial, help, def_text)
        main_sizer.Add(inp_sizer, 1, wx.ALL | wx.EXPAND, 5)
        main_sizer.Add(ok_cancel(self), 0, wx.ALL | wx.EXPAND, 5)
        self.SetSizer(main_sizer)
        main_sizer.SetSizeHints(self)
        # Make ENTER finish it
        self.Bind(wx.EVT_CHAR_HOOK, self.OnKey)

    def OnKey(self, event):
        """ Called by the dialog OnCharHook """
        if event.GetKeyCode() == wx.WXK_RETURN:
            self.EndModal(wx.ID_OK)
        else:
            # Not our key, continue processing it
            event.Skip()


class DataTypeList(DataTypeBase):
    def get_widget(self, obj, parent, entry, level):
        self.label = entry.name
        self.help = entry.help
        self.parent = parent
        self.entry = entry

        main_sizer = wx.StaticBoxSizer(wx.VERTICAL, parent, entry.name)
        sp = main_sizer.GetStaticBox()
        if entry.is_basic:
            sp.SetFont(get_emp_font())
        abm_sizer = wx.BoxSizer(wx.HORIZONTAL)

        list_sizer = wx.BoxSizer(wx.VERTICAL)
        self.lbox = wx.ListBox(sp, choices=[], size=wx.Size(def_text, -1), style=wx.LB_NEEDED_SB | wx.LB_SINGLE)
        try:
            self.set_items(obj, entry.name)
        except Exception:
            logger.error(f'{entry.name} {getattr(obj, entry.name)}')
            raise
        self.lbox.SetToolTip(self.help)
        list_sizer.Add(self.lbox, 1, wx.ALL | wx.EXPAND, 5)

        abm_sizer.Add(list_sizer, 1, wx.EXPAND, 5)

        but_sizer = wx.BoxSizer(wx.VERTICAL)
        self.b_up = wx.BitmapButton(sp, style=wx.BU_AUTODRAW, bitmap=get_btn_bitmap("arrow-up"))
        self.b_up.SetToolTip("Move the selection up")
        but_sizer.Add(self.b_up, 0, wx.ALL, 5)
        self.b_down = wx.BitmapButton(sp, style=wx.BU_AUTODRAW, bitmap=get_btn_bitmap("arrow-down"))
        self.b_down.SetToolTip("Move the selection down")
        but_sizer.Add(self.b_down, 0, wx.ALL, 5)
        self.b_add = wx.BitmapButton(sp, style=wx.BU_AUTODRAW, bitmap=get_btn_bitmap("plus"))
        self.b_add.SetToolTip("Add one entry")
        but_sizer.Add(self.b_add, 0, wx.ALL, 5)
        self.b_remove = wx.BitmapButton(sp, style=wx.BU_AUTODRAW, bitmap=get_btn_bitmap("minus"))
        self.b_remove.SetToolTip("Remove the entry")
        but_sizer.Add(self.b_remove, 0, wx.ALL, 5)

        abm_sizer.Add(but_sizer, 0, 0, 5)
        main_sizer.Add(abm_sizer, 1, wx.EXPAND, 5)

        self.b_up.Bind(wx.EVT_BUTTON, lambda event: move_sel_up(self.lbox))
        self.b_down.Bind(wx.EVT_BUTTON, lambda event: move_sel_down(self.lbox))
        self.b_add.Bind(wx.EVT_BUTTON, self.OnAdd)
        self.b_remove.Bind(wx.EVT_BUTTON, lambda event: remove_item(self.lbox))

        self.lbox.Bind(wx.EVT_LISTBOX_DCLICK, self.OnDClick)
        return main_sizer

    def OnDClick(self, event):
        index, string, obj = get_selection(self.lbox)
        if index == wx.NOT_FOUND:
            return
        self.edit_item(string, obj, index)

    def create_edit_title(self, index):
        if index == -1:
            return f'New {self.label} entry'
        return f'Edit {self.label} entry {index+1}'

    def OnAdd(self, event):
        self.edit_item()


class DataTypeListString(DataTypeList):
    def set_items(self, obj, member):
        val = getattr(obj, member)
        if val is None or isinstance(val, type):
            val = []
        self.lbox.SetItems(val)

    def edit_item(self, string='', obj=None, index=-1):
        dlg = InputStringDialog(self.parent, self.label, self.create_edit_title(index), self.help, initial=string)
        res = dlg.ShowModal()
        if res == wx.ID_OK:
            if index == -1:
                self.lbox.Append(dlg.input.Value)
            else:
                self.lbox.SetString(index, dlg.input.Value)
        dlg.Destroy()

    def get_value(self):
        return [self.lbox.GetString(n) for n in range(self.lbox.GetCount())]


class DataTypeListDict(DataTypeList):
    def set_items(self, obj, member):
        val = getattr(obj, member)
        if val is None or isinstance(val, type):
            val = []
        set_items(self.lbox, val)

    def edit_item(self, string='', obj=None, index=-1):
        if obj is None:
            obj = self.entry.cls()
        res = edit_dict(self.parent.Parent, obj, self.entry.sub, self.entry.name, self.create_edit_title(index))
        if res == wx.ID_OK:
            if index == -1:
                self.lbox.Append(str(obj), obj)
            else:
                self.lbox.SetString(index, str(obj))

    def get_value(self):
        return get_client_data(self.lbox)


class DummyForList(object):
    def __init__(self, member, initial):
        setattr(self, member, initial)


class DataTypeListListString(DataTypeListDict):
    def edit_item(self, string='', obj=None, index=-1):
        # Here we create a dummy object with a data member named with the same name as the list
        # We then use the "dict" edition
        name = self.entry.name
        valids = [DataTypeListString('list(string)', self.restriction, self.default)]
        new_entries = [DataEntry(name, valids, None, self.help)]
        new_obj = DummyForList(name, [] if obj is None else obj)
        res = edit_dict(self.parent.Parent, new_obj, new_entries, self.entry.name, self.create_edit_title(index))
        if res == wx.ID_OK:
            new_val = getattr(new_obj, name)
            if index == -1:
                self.lbox.Append(str(new_val), new_val)
            else:
                self.lbox.SetString(index, str(new_val))


# ##################################################################################################
#  End of DataType* classes
# ##################################################################################################


class EditDict(wx.Dialog):
    """ Dialog for a group of options """
    def __init__(self, parent, o, title, data_tree=None):
        # Generated code
        wx.Dialog.__init__(self, parent, title=title,
                           style=wx.STAY_ON_TOP | wx.BORDER_DEFAULT | wx.CAPTION)  # wx.RESIZE_BORDER
        self.parent = parent
        self.obj = o
        # Main sizer
        b_sizer = wx.BoxSizer(wx.VERTICAL)
        # Output widgets sizer
        middle_sizer = wx.BoxSizer(wx.HORIZONTAL)
        # This is the area for the output widgets
        self.scrollWindow = wx.ScrolledWindow(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.VSCROLL)
        self.scrollWindow.SetScrollRate(15, 15)

        # Main widgets area, scrollable
        self.scrl_sizer = wx.BoxSizer(wx.VERTICAL)
        self.data_type_tree = get_data_type_tree(RegOutput.get_class_for(o.type)()) if data_tree is None else data_tree
        add_widgets(o, self.data_type_tree, self.scrollWindow, self.scrl_sizer)
        self.scrollWindow.SetSizer(self.scrl_sizer)
        self.compute_scroll_hints()
        self.scrl_sizer.Fit(self.scrollWindow)
        self.scrollWindow.SetAutoLayout(True)
        middle_sizer.Add(self.scrollWindow, 1, wx.EXPAND | wx.ALL, 5)
        # Add the outputs are to the main sizer
        b_sizer.Add(middle_sizer, 1, wx.ALL | wx.EXPAND, 5)

        # Standard Ok/Cancel button
        b_sizer.Add(ok_cancel(self), 0, wx.ALL | wx.EXPAND, 5)

        # Resize things when the collapsible panes change their state
        self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.OnResize)

        # Add the main sizer to the dialog
        self.SetSizer(b_sizer)
        b_sizer.SetSizeHints(self)

        # Auto doesn't work here, we want to adjust the size hints before
        # self.SetAutoLayout(True)
        # b_sizer.Fit(self)

        self.Layout()
        self.Centre(wx.BOTH)
        self.old_size = self.GetSize()

        self.delta = self.old_size-self.GetClientRect().Size

    def compute_scroll_hints(self):
        """ Adjust the scroller size hints according to the content and the display """
        maxDisplayArea = wx.Display().GetClientArea()
        max_usable_height = maxDisplayArea.Height - 200
        max_usable_width = maxDisplayArea.Width
        min_scroller_size = wx.Size(min(self.scrl_sizer.MinSize.width, max_usable_width),
                                    min(self.scrl_sizer.MinSize.height, max_usable_height))
        self.scrollWindow.SetSizeHints(min_scroller_size, wx.Size(min_scroller_size.width, -1))

    def OnResize(self, event):
        self.compute_scroll_hints()
        sizer = self.GetSizer()
        sizer.Layout()
        # Not working ... why?
        new_size = sizer.MinSize+self.delta
        self.SetSize(new_size)

    def get_values(self):
        for entry in self.data_type_tree:
            if entry.name == 'type':
                continue
            setattr(self.obj, entry.name, entry.valids[0].get_value())

    def __del__(self):
        pass


def edit_dict(parent_dialog, obj, entries, entry_name, title=None):
    if title is None:
        title = parent_dialog.GetTitle() + ' | ' + entry_name
    dlg = EditDict(parent_dialog, obj, title, entries)
    res = dlg.ShowModal()
    if res == wx.ID_OK:
        dlg.get_values()
    dlg.Destroy()
    return res


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
    elif kind == 'list(string)':
        return DataTypeListString
    elif kind == 'list(dict)':
        return DataTypeListDict
    elif kind == 'list(list(string))':
        return DataTypeListListString
    return DataTypeBase


def add_widgets(obj, entries, parent, sizer, level=0):
    if isinstance(obj, type):
        logger.error(f'- !!! {obj.__dict__} {type(obj)}')
        return

    # Compute the len for the largest label
    font = wx.StaticText(parent).GetFont()
    dc = wx.ScreenDC()
    dc.SetFont(font)
    dc_emp = wx.ScreenDC()
    dc_emp.SetFont(get_emp_font())
    global max_label
    cur_max = max_label
    # TODO: the label can include restrictions, must be adjusted
    # TODO: GetTextExtent failing on bold!!!
    max_label = max((int(dc_emp.GetTextExtent(e.name).width*1.15) if e.is_basic else
                    dc.GetTextExtent(e.name).width for e in entries))
    # This is also wrong:
    # max2 = max((parent.GetFullTextExtent(e.name, (get_emp_font() if e.is_basic else None)) for e in entries))
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
    def __init__(self, name, valids, def_val, help, is_basic):
        self.name = name
        self.valids = valids
        self.def_val = def_val
        self.help = '\n'.join((ln.strip() for ln in help.splitlines(True)))
        self.is_dict = any((x.is_dict for x in valids))
        self.is_basic = is_basic


def get_data_type_tree(obj):
    """ Create a tree containing all the DataEntry objects associated to the data in the *obj* output """
    entries = []
    # TODO: move this to Optionable
    m1 = dict(obj.get_attrs_gen())
    m2 = dict(filter(lambda k: k[0][0] != '_', vars(obj).items()))
    diff = set(m2) - set(m1)
    if len(diff) != 0:
        logger.error(diff)
        logger.error(m1)
        logger.error(m2)
    for k, v in m2.items():
        help, _, is_alias = obj.get_doc(k)
        if help is None or is_alias:
            if not is_alias:
                logger.error(k)
            continue
        is_basic = False
        if help[0] == '*':
            help = help[1:]
            is_basic = True
        case = f'{k} = `{v}`'
        assert help[0] == '[', case
        valid, extra, def_val, real_help = obj.get_valid_types(help)
        valids = [get_class_for(v, e)(v, e, def_val) for v, e in zip(valid, extra)]
        case += f' {extra} """ {help} """'
        assert valids, case
        valids = sorted(valids, key=lambda x: 200-TYPE_PRIORITY[x.kind])
        entry = DataEntry(k, valids, def_val, real_help, is_basic)
        if entry.is_dict:
            entry.sub = get_data_type_tree(v())
            entry.cls = v
        entries.append(entry)
    return entries
