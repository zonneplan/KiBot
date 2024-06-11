# Classes to edit the different data types used for the YAML config
# Each class should provide a suitable widget

from copy import deepcopy
import math
import wx
from .validators import NumberValidator
from .gui_helpers import (move_sel_up, move_sel_down, ok_cancel, remove_item, input_label_and_text, get_client_data, set_items,
                          get_selection, get_emp_font, pop_error, add_abm_buttons, get_res_bitmap, pop_confirm)
from . import gui_helpers as gh
from .gui_config import USE_DIALOG_FOR_NESTED, TYPE_SEL_RIGHT
from ..error import KiPlotConfigurationError
from ..misc import typeof, try_int
from ..optionable import Optionable
from .. import log
logger = log.get_logger()
TYPE_PRIORITY = {'list(dict|string)': 110, 'list(dict)': 100, 'list(list(string))': 90, 'list(string)': 80, 'dict': 60,
                 'string_dict': 55, 'string': 50, 'number': 20, 'boolean': 10}
TYPE_ABREV = {'list(dict|string)': 'LDS', 'list(dict)': 'LD', 'list(list(string))': 'LLS', 'list(string)': 'LS', 'dict': 'D',
              'string_dict': 'SD', 'string': 'S', 'number': 'N', 'boolean': 'B'}
TYPE_EMPTY = {'list(dict|string)': [], 'list(dict)': [], 'list(list(string))': [], 'list(string)': [], 'dict': {},
              'string_dict': {}, 'string': '', 'number': '', 'boolean': False}
max_label = 200
def_text = 200
BMP_CLEAR = wx.ART_DELETE
# BMP_CLEAR = wx.ART_CROSS_MARK


class DataTypeBase(object):
    def __init__(self, kind, restriction, default, name):
        self.kind = kind
        self.restriction = restriction
        self.default = self.reset_value = default
        self.is_dict = kind == 'dict'
        self.is_list_dict = kind == 'list(dict)' or kind == 'list(dict|string)'

    def get_widget(self, obj, parent, entry, level, init, value):
        entry.edited = False
        help = entry.help
        if self.default is not None:
            help += f'\nDefault: {self.default}'
        e_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.label = wx.StaticText(parent, label=self.get_label(entry), size=wx.Size(max_label, -1), style=wx.ALIGN_RIGHT)
        entry.show_status(self.label)
        self.label.SetToolTip(help)
        self.define_input(parent, value, init)
        self.input.SetToolTip(help)

        e_sizer.Add(self.label, gh.SIZER_FLAGS_0)
        e_sizer.Add(self.input, gh.SIZER_FLAGS_1)
        self.entry = entry
        self.input.Bind(wx.EVT_TEXT, self.OnChange)
        return e_sizer

    def get_restriction_help(self):
        return ''

    def get_label(self, entry):
        return entry.name

    def get_value(self):
        return self.input.Value

    def focus(self):
        self.input.SetFocus()

    def reset(self, get_focus=True):
        self.entry.set_edited(False, self.label)
        self.ori_value = self.input.Value = self.reset_value
        if get_focus:
            self.focus()

    def OnChange(self, event):
        self.entry.set_edited(self.input.Value != self.ori_value, self.label)


class DataTypeString(DataTypeBase):
    def define_input(self, parent, value, init):
        self.input = wx.TextCtrl(parent, size=wx.Size(def_text, -1))
        if init:
            self.input.SetValue(value)
        self.ori_value = self.input.Value
        self.input.Bind(wx.EVT_TEXT, self.OnChange)


class DataTypeNumber(DataTypeString):
    def __init__(self, kind, restriction, default, name):
        super().__init__(kind, restriction, default, name)
        self.has_min = False
        self.has_max = False
        if restriction is None:
            restriction = (-math.inf, math.inf)
        else:
            if restriction[0] is None:
                restriction[0] = -math.inf
            else:
                self.has_min = True
            if restriction[1] is None:
                restriction[1] = math.inf
            else:
                self.has_max = True
        self.restriction = restriction
        try:
            self.reset_value = str(try_int(self.default))
        except TypeError:
            logger.error(f'Missing default for {name}')
            self.reset_value = '0'

    def get_widget(self, obj, parent, entry, level, init, value):
        if init:
            value = str(value)
        sizer = super().get_widget(obj, parent, entry, level, init, value)
        self.input.SetValidator(NumberValidator(self.input, self.restriction, self.default, self.OnChange))
        return sizer

    def get_label(self, entry):
        if not self.has_min and not self.has_max:
            return entry.name
        return entry.name + f' [{self.restriction[0]},{self.restriction[1]}]'

    def get_restriction_help(self):
        return f'\nRange: {self.restriction[0]} to {self.restriction[1]}'

    def get_value(self):
        val = self.input.Value
        if val == '-' or val == '':
            return self.default
        return try_int(val)


class DataTypeBoolean(DataTypeBase):
    def define_input(self, parent, value, init):
        self.input = wx.CheckBox(parent)
        if init:
            self.input.SetValue(value)
        self.ori_value = self.input.Value
        self.input.Bind(wx.EVT_CHECKBOX, self.OnChange)


class DataTypeChoice(DataTypeBase):
    def define_input(self, parent, value, init):
        self.input = wx.Choice(parent, choices=self.restriction)
        if init:
            try:
                self.input.SetSelection(self.restriction.index(value))
            except ValueError:
                # New entry
                self.input.SetSelection(0)
        self.ori_value = self.input.Selection
        self.input.Bind(wx.EVT_CHOICE, self.OnChange)

    def get_value(self):
        # Why not GetValue??!!
        return self.restriction[self.input.GetSelection()]

    def reset(self, get_focus=True):
        self.entry.set_edited(False, self.label)
        if self.default is None:
            logger.error(f'Missing default for {self.entry.name}')
        self.reset_value = self.restriction.index(self.default) if self.default is not None else 0
        self.ori_value = self.input.Selection = self.reset_value
        if get_focus:
            self.focus()

    def OnChange(self, event):
        self.entry.set_edited(self.input.Selection != self.ori_value, self.label)


class DataTypeNumberChoice(DataTypeChoice):
    def __init__(self, kind, restriction, default, name):
        super().__init__(kind, restriction, default, name)
        self.restriction = self.restriction[1]
        self.default = str(self.default)

    def define_input(self, parent, value, init):
        super().define_input(parent, str(value), init)

    def get_value(self):
        return float(super().get_value())


class DataTypeCombo(DataTypeBase):
    def define_input(self, parent, value, init):
        self.input = wx.ComboBox(parent, choices=[v for v in self.restriction if v != '*'])
        if init:
            self.input.SetValue(value)
        self.ori_value = self.input.Value
        self.input.Bind(wx.EVT_TEXT, self.OnChange)


class DataTypeDict(DataTypeBase):
    def get_widget(self, obj, parent, entry, level, init, value):
        entry.edited = False
        help = entry.help
        lbl = self.get_label(entry)
        # Use the current value only when "init", otherwise use an empty object
        if init:
            self.sub_obj = getattr(obj, entry.name)
        else:
            self.sub_obj = entry.cls()
            self.sub_obj.config(obj)
        # self.ori_value = deepcopy(self.sub_obj._tree)
        self.sub_entries = entry.sub
        self.parent = parent
        self.entry = entry
        self.obj = obj
        e_sizer = wx.BoxSizer(wx.HORIZONTAL)

        if USE_DIALOG_FOR_NESTED:
            self.entry_name = lbl
            self.btn = wx.Button(parent, label="Edit "+lbl)
            e_sizer.Add(self.btn, gh.SIZER_FLAGS_1)
            self.btn.Bind(wx.EVT_BUTTON, self.OnEdit)
        else:
            # Collapsible pane version
            cp = wx.CollapsiblePane(parent, label=lbl)
            cp.SetToolTip(help)
            # cp.Collapse(False)  # Start expanded

            pane = cp.GetPane()
            pane_sizer = wx.BoxSizer(wx.VERTICAL)

            add_widgets(self.sub_obj, entry.sub, pane, pane_sizer, level+1)
            pane.SetSizer(pane_sizer)

            e_sizer.Add(cp, gh.SIZER_FLAGS_1)
            self.pane = pane
        return e_sizer

    def OnEdit(self, event):
        if edit_dict(self.parent.Parent, self.sub_obj, self.sub_entries, self.entry_name):
            self.entry.set_edited(True)

    def focus(self):
        if USE_DIALOG_FOR_NESTED:
            self.btn.SetFocus()
        else:
            self.pane.SetFocus()

    def reset(self, get_focus=True):
        self.entry.set_edited(False)
        # self.ori_value = {}
        self.sub_obj = self.entry.cls()
        self.sub_obj.config(self.obj)
        if get_focus:
            self.focus()

    def get_value(self):
        if USE_DIALOG_FOR_NESTED:
            tree = self.sub_obj._tree
        else:
            tree = {}
            for e in self.sub_entries:
                if e.user_defined:
                    tree[e.name] = e.get_value()
        # logger.error(tree)
        return tree


class InputStringDialog(wx.Dialog):
    def __init__(self, parent, lbl, title, help, initial=''):
        wx.Dialog.__init__(self, parent, title=title,
                           style=wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        _, self.input, inp_sizer = input_label_and_text(self, lbl, initial, help, def_text)
        main_sizer.Add(inp_sizer, gh.SIZER_FLAGS_1)
        main_sizer.Add(ok_cancel(self), gh.SIZER_FLAGS_0)
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
    def get_widget(self, obj, parent, entry, level, init, value):
        entry.edited = False
        self.label = entry.name
        self.help = entry.help
        self.parent = parent
        self.entry = entry

        main_sizer = wx.StaticBoxSizer(wx.VERTICAL, parent, entry.name)
        self.sp = main_sizer.GetStaticBox()
        entry.show_status(self.sp)
        abm_sizer = wx.BoxSizer(wx.HORIZONTAL)

        list_sizer = wx.BoxSizer(wx.VERTICAL)
        self.lbox = wx.ListBox(self.sp, choices=[], size=wx.Size(def_text, -1), style=wx.LB_NEEDED_SB | wx.LB_SINGLE)
        if init:
            try:
                self.set_items(obj, entry.name)
            except Exception:
                logger.error(f'{entry.name} {getattr(obj, entry.name)}')
                raise
        self.ori_value = self.get_value()
        self.lbox.SetToolTip(self.help)
        list_sizer.Add(self.lbox, gh.SIZER_FLAGS_1)

        abm_sizer.Add(list_sizer, gh.SIZER_FLAGS_1_NO_BORDER)
        abm_sizer.Add(add_abm_buttons(self, self.sp), gh.SIZER_FLAGS_0_NO_EXPAND)
        main_sizer.Add(abm_sizer, gh.SIZER_FLAGS_1_NO_BORDER)

        self.but_up.Bind(wx.EVT_BUTTON, self.OnUp)
        self.but_down.Bind(wx.EVT_BUTTON, self.OnDown)
        self.but_add.Bind(wx.EVT_BUTTON, lambda event: self.edit_item())
        self.but_remove.Bind(wx.EVT_BUTTON, self.OnRemove)

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

    def mark_edited(self):
        cur_value = self.get_value()
        self.entry.set_edited(cur_value != self.ori_value, self.sp)

    def focus(self):
        self.lbox.SetFocus()

    def reset(self, get_focus=True):
        self.entry.set_edited(False, self.sp)
        self.lbox.SetItems([])
        if get_focus:
            self.focus()

    def OnUp(self, event):
        move_sel_up(self.lbox)
        self.mark_edited()

    def OnDown(self, event):
        move_sel_down(self.lbox)
        self.mark_edited()

    def OnRemove(self, event):
        remove_item(self.lbox)
        self.mark_edited()


class DataTypeListString(DataTypeList):
    def set_items(self, obj, member):
        val = getattr(obj, member)
        if val is None or isinstance(val, type):
            val = []
        self.lbox.SetItems(val)

    def edit_item(self, string='', obj=None, index=-1):
        ori = string
        dlg = InputStringDialog(self.parent, self.label, self.create_edit_title(index), self.help, initial=string)
        res = dlg.ShowModal()
        if res == wx.ID_OK:
            if index == -1:
                self.lbox.Append(dlg.input.Value)
                self.mark_edited()
            elif ori != dlg.input.Value:
                self.lbox.SetString(index, dlg.input.Value)
                self.mark_edited()
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
        res = edit_dict(self.parent.Parent, obj, self.entry.sub, self.entry.name, self.create_edit_title(index),
                        force_changed=True)
        if res:
            if index == -1:
                self.lbox.Append(str(obj), obj)
            else:
                self.lbox.SetString(index, str(obj))
            self.entry.set_edited(True)

    def get_value(self):
        return [v._tree for v in get_client_data(self.lbox)]


class DummyForDictOrString(object):
    def __init__(self, member, initial, cls):
        if initial is None:
            setattr(self, member, cls)
            self._tree = {}  # Start indicating isn't from user
        else:
            setattr(self, member, initial)
            self._tree = {member: initial if isinstance(initial, str) else initial._tree}

    def reconfigure(self, tree):
        self._tree = tree
        k, v = tuple(tree.items())[0]
        if isinstance(v, str):
            setattr(self, k, v)
        else:
            obj = getattr(self, k)
            obj.reconfigure(v)


class DataTypeListDictOrString(DataTypeListDict):
    def edit_item(self, string='', obj=None, index=-1):
        name = self.entry.name
        str_cls = get_class_for('string', self.restriction)
        valids = [str_cls('string', self.restriction, self.default),
                  DataTypeDict('dict', self.restriction, self.default)]
        new_obj = DummyForDictOrString(name, obj, self.entry.cls())
        new_obj._parent = self.entry.obj._parent
        new_entry = DataEntry(name, valids, None, self.help, False, new_obj, 0)
        new_entry.sub = self.entry.sub
        new_entry.cls = self.entry.cls
        res = edit_dict(self.parent.Parent, new_obj, [new_entry], name, self.create_edit_title(index))
        if res:
            new_val = getattr(new_obj, name)
            if index == -1:
                self.lbox.Append(str(new_val), new_val)
            else:
                self.lbox.SetString(index, str(new_val))
                self.lbox.SetClientData(index, new_val)
            self.mark_edited()

    def get_value(self):
        return [v if isinstance(v, str) else v._tree for v in get_client_data(self.lbox)]


class StringPair(object):
    def __init__(self, key=None, value=None):
        if key is None:
            self.key = 'new_key'
            self.value = 'new_value'
            self._tree = {}  # Start indicating isn't from user
        else:
            self.key = key
            self.value = value
            self._tree = {'key': key, 'value': value}

    def config(self, name):
        self.key = self._tree.get('key', self.key)
        self.value = self._tree.get('value', self.value)
        if not self.key:
            raise KiPlotConfigurationError("The `key` can't be empty")

    def __repr__(self):
        return f'{self.key} -> {self.value}'


class DataTypeStringDict(DataTypeList):
    """ Class to edit a pair key/value
        Behaves like an Optionable """
    def set_items(self, obj, member):
        val = getattr(obj, member)
        if val is None or isinstance(val, type):
            val = {}
        set_items(self.lbox, [StringPair(k, v) for k, v in val.items()])

    def edit_item(self, string='', obj=None, index=-1):
        new_obj = StringPair() if obj is None else obj
        new_entries = [DataEntry('key', [DataTypeString('string', None, '')], None, self.help, False, new_obj, 0),
                       DataEntry('value', [DataTypeString('string', None, '')], None, self.help, False, new_obj, 0)]
        res = edit_dict(self.parent.Parent, new_obj, new_entries, self.entry.name, self.create_edit_title(index))
        if res:
            if index == -1:
                self.lbox.Append(str(new_obj), new_obj)
            else:
                self.lbox.SetString(index, str(new_obj))
            self.entry.set_edited(True)

    def get_value(self):
        return {v.key: v.value for v in get_client_data(self.lbox)}


class DummyForList(object):
    def __init__(self, member, initial):
        setattr(self, member, initial)
        self._tree = {}  # Start indicating isn't from user


class DataTypeListListString(DataTypeListDict):
    def edit_item(self, string='', obj=None, index=-1):
        # Here we create a dummy object with a data member named with the same name as the list
        # We then use the "dict" edition
        name = self.entry.name
        valids = [DataTypeListString('list(string)', self.restriction, self.default)]
        new_obj = DummyForList(name, [] if obj is None else obj)
        new_entries = [DataEntry(name, valids, None, self.help, False, new_obj, 0)]
        res = edit_dict(self.parent.Parent, new_obj, new_entries, self.entry.name, self.create_edit_title(index))
        if res:
            new_val = getattr(new_obj, name)
            # logger.error(new_val)
            if index == -1:
                self.lbox.Append(str(new_val), new_val)
            else:
                self.lbox.SetString(index, str(new_val))
                self.lbox.SetClientData(index, new_val)
            self.mark_edited()

    def get_value(self):
        return get_client_data(self.lbox)


# ##################################################################################################
#  End of DataType* classes
# ##################################################################################################


class EditDict(wx.Dialog):
    """ Dialog for a group of options """
    def __init__(self, parent, o, title, data_tree=None, validator=None):
        # Generated code
        wx.Dialog.__init__(self, parent, title=title,
                           style=wx.STAY_ON_TOP | wx.BORDER_DEFAULT | wx.CAPTION)  # wx.RESIZE_BORDER
        self.parent = parent
        self.obj = o
        self.validator = validator
        # Main sizer
        b_sizer = wx.BoxSizer(wx.VERTICAL)
        # Output widgets sizer
        middle_sizer = wx.BoxSizer(wx.HORIZONTAL)
        # This is the area for the output widgets
        self.scrollWindow = wx.ScrolledWindow(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.VSCROLL)
        self.scrollWindow.SetScrollRate(15, 15)

        # Main widgets area, scrollable
        self.scrl_sizer = wx.BoxSizer(wx.VERTICAL)
        self.data_type_tree = get_data_type_tree(o.__class__(), o) if data_tree is None else data_tree
        add_widgets(o, self.data_type_tree, self.scrollWindow, self.scrl_sizer)
        self.scrollWindow.SetSizer(self.scrl_sizer)
        self.compute_scroll_hints()
        self.scrl_sizer.Fit(self.scrollWindow)
        self.scrollWindow.SetAutoLayout(True)
        middle_sizer.Add(self.scrollWindow, gh.SIZER_FLAGS_1)
        # Add the outputs are to the main sizer
        b_sizer.Add(middle_sizer, gh.SIZER_FLAGS_1)

        # Standard Ok/Cancel button
        b_sizer.Add(ok_cancel(self, self.OnOK), gh.SIZER_FLAGS_0)

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

    def OnOK(self, event):
        self.changed, retry = self.update_values()
        if not retry:
            self.EndModal(wx.ID_OK)

    def update_values(self):
        tree = {}
        for entry in self.data_type_tree:
            if entry.skip:
                tree['type'] = self.obj.type
                continue
            value = entry.get_value()
            if value is not None:
                tree[entry.name] = value
        if self.obj._tree == tree:
            logger.debug(f'Not modified {tree}')
            return False, False
        logger.debug(f'Updating {self.obj} {type(self.obj)} {tree}')
        # First try using a dummy
        dummy = deepcopy(self.obj)
        try:
            dummy.reconfigure(tree)
        except KiPlotConfigurationError as e:
            logger.debug(f'Error configuring: {e}')
            pop_error(str(e))
            # Ask to retry, the user can use Cancel because the original object isn't changed
            return True, True
        # Perform extra validations, i.e. usable name
        if self.validator:
            if not self.validator(dummy):
                return True, True
        # Ok, the configuration is valid, configure the real object
        self.obj.reconfigure(tree)
        # Transfer the new state to be the "original"
        for entry in self.data_type_tree:
            entry.update_value()
        return True, False


def edit_dict(parent_dialog, obj, entries, entry_name, title=None, validator=None, force_changed=False):
    if title is None:
        title = parent_dialog.GetTitle() + ' | ' + entry_name
    dlg = EditDict(parent_dialog, obj, title, entries, validator)
    changed = dlg.ShowModal() == wx.ID_OK and (dlg.changed or force_changed)
    dlg.Destroy()
    return changed


def get_class_for(kind, rest):
    """ Return a class suitable to edit data of the *kind* type. """
    if kind == 'string':
        if rest is not None:
            if '*' in rest:
                return DataTypeCombo
            return DataTypeChoice
        return DataTypeString
    elif kind == 'number':
        if rest and rest[0] == 'C':
            return DataTypeNumberChoice
        return DataTypeNumber
    elif kind == 'boolean':
        return DataTypeBoolean
    elif kind == 'string_dict':
        return DataTypeStringDict
    elif kind == 'dict':
        return DataTypeDict
    elif kind == 'list(string)':
        return DataTypeListString
    elif kind == 'list(dict)':
        return DataTypeListDict
    elif kind == 'list(dict|string)':
        return DataTypeListDictOrString
    elif kind == 'list(list(string))':
        return DataTypeListListString
    logger.error(f'Not implemented: {kind}')
    raise AssertionError()


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
    # TODO: GetTextExtent failing on bold!!!
    max_label = max((int(dc_emp.GetTextExtent(e.get_label()).width*1.15) if e.is_basic else
                    dc.GetTextExtent(e.get_label()).width for e in entries))
    # This is also wrong:
    # max2 = max((parent.GetFullTextExtent(e.name, (get_emp_font() if e.is_basic else None)) for e in entries))
    # Size for input boxes
    global def_text
    def_text = dc.GetTextExtent('M'*40).width

    # logger.error(f'{obj._tree}')
    for entry in entries:
        if not entry.skip:
            entry.add_widgets(obj, parent, sizer, level)
    max_label = cur_max


class DataEntry(object):
    """ Class to represent one data value to be edited """
    def __init__(self, name, valids, def_val, help, is_basic, obj, level):
        self.name = name
        self.valids = valids
        self.def_val = def_val
        self.help = '\n'.join((ln.strip() for ln in help.splitlines(True)))
        self.is_dict = any((x.is_dict for x in valids))
        self.is_list_dict = any((x.is_list_dict for x in valids))
        self.is_basic = is_basic
        self.selected = 0
        self.edited = False
        self.obj = obj
        self.skip = self.name == 'type' and level == 0
        self.select_data_type(obj, level)

    def select_data_type(self, obj, level=0):
        # Solve the current value
        user_value = obj._tree.get(self.name)
        if user_value is not None:
            # The user provided a value
            self.user_defined = True
            if isinstance(user_value, (dict, list)):
                # For complex data types we get the configured value
                # They will extract data from the tree
                self.ori_val = getattr(obj, self.name)
            else:
                # If the data is simple, get it from the tree, so the user sees the same found in the YAML
                self.ori_val = user_value
        else:
            # No user provided value
            self.user_defined = False
            # Get the current value in the object
            self.ori_val = getattr(obj, self.name)
            selected, _ = self.get_used_data_type(self.ori_val)
            # Is this usable?
            if self.ori_val is None or isinstance(self.ori_val, type) or selected == -1:
                # Nope, use the default
                self.ori_val = self.def_val
        self.user_defined_ori = self.user_defined
        self.selected, data_type = self.get_used_data_type(self.ori_val)
        if self.selected == -1:  # I.e. optionable not used and hence is None
            self.selected = 0
            self.ori_val = TYPE_EMPTY[self.valids[0].kind]
        logger.debug(f'{" "*level*2}- {self.name} ori:{self.ori_val} user:{self.user_defined} {data_type} sel:{self.selected}')

    def get_label(self):
        return self.valids[0].get_label(self)

    def show_status(self, label):
        if self.is_basic:
            label.SetFont(get_emp_font())
        if self.user_defined:
            label.SetForegroundColour(gh.USER_EDITED_COLOR)
        else:
            label.SetForegroundColour(self.ori_fore_color)

    def get_used_data_type(self, value):
        data_type = typeof(value, Optionable)
        return next((c for c, v in enumerate(self.valids) if v.kind == data_type), -1), data_type

    def add_widgets(self, obj, parent, sizer, level):
        """ Add a widget for each possible data type.
            Also add a control to change the data type.
            Here we bind the entry to the real object, during creation we just got a template (the class) """
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        is_first = True
        if obj != self.obj:
            # This is common for lists
            self.select_data_type(obj)
            self.obj = obj
        self.widgets = []
        for c, valid in enumerate(self.valids):
            if is_first:
                if len(self.valids) > 1:
                    # Choice to select the data type when multiple are allowed
                    sel = wx.Choice(parent, choices=[TYPE_ABREV[v.kind] for v in self.valids],
                                    size=wx.Size(int(def_text/8), -1))
                    sel.SetSelection(self.selected)
                    sel.Bind(wx.EVT_CHOICE, self.OnChoice)
                else:
                    # Just a hint abou the data type
                    sel = wx.StaticText(parent, label=TYPE_ABREV[valid.kind], size=wx.Size(60, -1),
                                        style=wx.ALIGN_CENTER)
                # Button to clear the data, and remove it from the YAML
                clr = wx.BitmapButton(parent, bitmap=get_res_bitmap(BMP_CLEAR))
                clr.SetToolTip(f'Reset {self.name}')
                clr.Bind(wx.EVT_BUTTON, self.OnRemove)
                self.ori_fore_color = sel.GetForegroundColour()
                if not TYPE_SEL_RIGHT:
                    flgs = wx.SizerFlags().Border(wx.RIGHT).Center()
                    self.sizer.Add(sel, flgs)
                    self.sizer.Add(clr, flgs)
                self.sel_widget = sel
                self.clr_widget = clr
            is_selected = c == self.selected
            e_sizer = valid.get_widget(obj, parent, self, level, is_selected, self.ori_val)
            self.sizer.Add(e_sizer, gh.SIZER_FLAGS_1_NO_BORDER)
            self.widgets.append(e_sizer)
            if not is_selected:
                self.sizer.Show(e_sizer, False)
            is_first = False
        if TYPE_SEL_RIGHT:
            flgs = wx.SizerFlags().Border(wx.LEFT).Center()
            self.sizer.Add(sel, flgs)
            self.sizer.Add(clr, flgs)
        if self.user_defined:
            sel.SetForegroundColour(gh.USER_EDITED_COLOR)
        else:
            clr.Disable()
        self.set_sel_tooltip()
        sizer.Add(self.sizer, gh.SIZER_FLAGS_0_NO_BORDER)
        self.parent_sizer = sizer
        self.window = parent

    def set_edited(self, edited, widget=None):
        new_user_defined = edited or self.user_defined_ori
        self.edited = edited
        if new_user_defined == self.user_defined:
            return False
        self.user_defined = new_user_defined
        self.sel_widget.SetForegroundColour(gh.USER_EDITED_COLOR if new_user_defined else self.ori_fore_color)
        self.clr_widget.Enable(new_user_defined)
        if widget:
            self.show_status(widget)
        return True

    def get_value(self):
        return self.valids[self.selected].get_value() if self.user_defined else None

    def update_value(self):
        if not self.user_defined or not self.edited:
            return
        self.ori_val = self.get_value()

    def set_sel_tooltip(self):
        if len(self.valids) == 1:
            sel_tooltip = f'{TYPE_ABREV[self.valids[0].kind]}: {self.valids[0].kind}'
        else:
            sel_tooltip = ''
            for c, valid in enumerate(self.valids):
                sel_tooltip += ('→' if c == self.selected else '   ') + f' {TYPE_ABREV[valid.kind]}: {valid.kind}\n'
            sel_tooltip = sel_tooltip[:-1]
        self.sel_widget.SetToolTip(sel_tooltip)

    def OnChoice(self, event):
        """ A new data type was selected.
            Hide the current widget and show the new one """
        self.sizer.Show(self.widgets[self.selected], False)
        self.selected = self.sel_widget.GetSelection()
        self.sizer.Show(self.widgets[self.selected], True)
        self.set_sel_tooltip()
        # The selected widget might be bigger, adjust the dialog
        self.window.Parent.OnResize(None)

    def OnRemove(self, event):
        if pop_confirm(f'Remove the data from {self.name}?'):
            self.user_defined_ori = False
            self.valids[self.selected].reset()


def adapt_default(val, name):
    if val is None:
        pass
    elif val[0] == "'" and val[-1] == "'":
        val = val[1:-1]
    elif val == '[]':
        val = []
    elif val == '{}':
        val = {}
    elif val == 'true':
        val = True
    elif val == 'false':
        val = False
    elif val[0] in {'-', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0'}:
        val = float(val)
    else:
        logger.error(f'Unknown default data type `{val}` for `{name}`')
    return val


def join_lists(valid, extra):
    # When we have things like list(dict)|list(string) in practice it means list(dict|string)
    # So here we apply this conversion
    list_index = None
    new_valid = []
    new_extra = []
    for c, (v, e) in enumerate(zip(valid, extra)):
        if v.startswith('list('):
            if list_index is None:
                # First list
                list_index = c
                v = v[:-1]
            else:
                # We have another list
                kind = v[5:-1]
                new_valid[list_index] += '|'+kind
                if e is not None:
                    assert new_extra[list_index] is None
                    new_extra[list_index] = e
                continue
        new_valid.append(v)
        new_extra.append(e)
    if list_index is not None:
        new_valid[list_index] += ')'
    return new_valid, new_extra


def get_data_type_tree(template, obj, level=0):
    """ Create a tree containing all the DataEntry objects associated to the data in the *obj* output """
    entries = []
    logger.debug(f'{" "*level*2}Starting data tree for {template.__repr__()} '
                 f'(type: {type(template)}) with {obj.__repr__()} as value')
    for k, v in template.get_attrs_gen():
        help, _, is_alias = template.get_doc(k)
        if help is None or is_alias:
            if not is_alias and k != 'type':
                logger.error(k)
            continue
        is_basic = False
        if help[0] == '*':
            help = help[1:]
            is_basic = True
        case = f'{k} = `{v}`'
        assert help[0] == '[', case
        valid, extra, def_val, real_help = template.get_valid_types(help)
        def_val = adapt_default(def_val, k)
        valid, extra = join_lists(valid, extra)
        valids = [get_class_for(v, e)(v, e, def_val, k) for v, e in zip(valid, extra)]
        case += f' {extra} """ {help} """'
        assert valids, case
        valids = sorted(valids, key=lambda x: 200-TYPE_PRIORITY[x.kind])
        obj_ref = obj
        if isinstance(obj, list):
            # list(dict)
            if len(obj) == 0:
                obj_ref = template
            else:
                obj_ref = obj[0]
        entry = DataEntry(k, valids, def_val, real_help, is_basic, obj_ref, level)
        if entry.is_dict:
            value = getattr(obj, k)
            reference = v()
            # if value is None or isinstance(value, type):
            if not isinstance(value, v):
                # If the current value is different use an empty object
                # I.e. something that can be a string or dict and is currently a string, then use a fresh dict
                value = reference
                logger.debug(f'{" "*level*2}- Using new object for {k}')
            entry.sub = get_data_type_tree(reference, value, level+1)
            entry.cls = v
        elif entry.is_list_dict:
            entry.cls = v
            o = v()
            entry.sub = get_data_type_tree(o, o, level+1)
        entries.append(entry)
    return entries
