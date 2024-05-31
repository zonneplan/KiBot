from copy import deepcopy
import os
import yaml
from .. import __version__
from .. import log
from ..kiplot import config_output
from ..registrable import RegOutput, Group, GroupEntry, RegFilter
from .data_types import edit_dict
from .gui_helpers import (move_sel_up, move_sel_down, remove_item, pop_error, get_client_data, pop_info, ok_cancel,
                          set_items, get_selection, init_vars, choose_from_list, add_abm_buttons, input_label_and_text,
                          set_button_bitmap)
from . import gui_helpers as gh
logger = log.get_logger()

import wx
# Do it before any wx thing is called
app = wx.App()
if hasattr(app, "GTKSuppressDiagnostics"):
    app.GTKSuppressDiagnostics()
if hasattr(wx, "APP_ASSERT_SUPPRESS"):
    app.SetAssertMode(wx.APP_ASSERT_SUPPRESS)
if hasattr(wx, "DisableAsserts"):
    wx.DisableAsserts()
if hasattr(wx, "GetLibraryVersionInfo"):
    WX_VERSION = wx.GetLibraryVersionInfo()  # type: wx.VersionInfo
    WX_VERSION = (WX_VERSION.Major, WX_VERSION.Minor, WX_VERSION.Micro)
else:
    # old kicad used this (exact version doesn't matter)
    WX_VERSION = (3, 0, 2)

OK_CHAR = '\U00002714'
# NOT_OK_CHAR = '\U0000274C'
NOT_OK_CHAR = '\U00002717'
init_vars()


def do_gui(outputs, cfg_file):
    for o in outputs:
        config_output(o)
    dlg = MainDialog(outputs, cfg_file)
    res = dlg.ShowModal()
    dlg.Destroy()
    return res


# ##########################################################################
# # Class MainDialog
# # The main dialog for the GUI
# ##########################################################################

class MainDialog(wx.Dialog):
    def __init__(self, outputs, cfg_file):
        wx.Dialog.__init__(self, None, title='KiBot '+__version__,  # size = wx.Size(463,529),
                           style=wx.DEFAULT_DIALOG_STYLE | wx.DIALOG_NO_PARENT | wx.STAY_ON_TOP | wx.BORDER_DEFAULT)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.notebook = wx.Notebook(self)
        main_sizer.Add(self.notebook, gh.SIZER_FLAGS_1)

        # Pages for the notebook
        self.outputs = OutputsPanel(self.notebook, outputs)
        self.notebook.AddPage(self.outputs, "Outputs")
        self.groups = GroupsPanel(self.notebook, outputs)
        self.notebook.AddPage(self.groups, "Groups")
        self.filters = FiltersPanel(self.notebook)
        self.notebook.AddPage(self.filters, "Filters")

        # Buttons
        but_sizer = wx.BoxSizer(wx.HORIZONTAL)
        # Save config
        self.but_save = wx.Button(self, label="Save config")
        self.but_save.Disable()
        set_button_bitmap(self.but_save, wx.ART_FILE_SAVE)
        but_sizer.Add(self.but_save, gh.SIZER_FLAGS_0_NO_EXPAND)
        # Separator
        but_sizer.Add((50, 0), gh.SIZER_FLAGS_1_NO_BORDER)
        # Run
        self.but_generate = wx.Button(self, label="Run")
        set_button_bitmap(self.but_generate, wx.ART_EXECUTABLE_FILE)
        self.but_generate.SetDefault()
        but_sizer.Add(self.but_generate, gh.SIZER_FLAGS_0_NO_EXPAND)
        # Cancel
        self.but_cancel = wx.Button(self, id=wx.ID_CANCEL, label="Cancel")
        but_sizer.Add(self.but_cancel, gh.SIZER_FLAGS_0_NO_EXPAND)
        main_sizer.Add(but_sizer, gh.SIZER_FLAGS_0_NO_BORDER)

        self.SetSizer(main_sizer)
        main_sizer.Fit(self)
        self.Centre(wx.BOTH)

        self.cfg_file = cfg_file
        self.edited = False

        # Connect Events
        self.but_save.Bind(wx.EVT_BUTTON, self.OnSave)
        self.but_generate.Bind(wx.EVT_BUTTON, self.OnGenerateOuts)
        # self.but_cancel.Bind(wx.EVT_BUTTON, self.OnExit)

    def refresh_groups(self):
        self.groups.refresh_groups()

    def mark_edited(self):
        if not self.edited:
            self.but_save.Enable(True)
        self.edited = True

    def OnGenerateOuts(self, event):
        # TODO: implement
        event.Skip()

    def OnSave(self, event):
        tree = {'kibot': {'version': 1}}
        # TODO: Should we delegate it to the class handling it?
        # Filters
        if self.filters.lbox.GetCount():
            tree['filters'] = [o._tree for o in get_client_data(self.filters.lbox)]
        # Groups: skipping outputs added from the output itself
        groups = RegOutput.get_groups_struct()
        if groups:
            grp_lst = []
            for name, gi in groups.items():
                items = [g.item for g in gi.items if g.defined_in()]
                if items:
                    grp_lst.append({'name': name, 'outputs': items})
            if grp_lst:
                tree['groups'] = grp_lst
        tree['outputs'] = [o._tree for o in get_client_data(self.outputs.lbox)]
        if os.path.isfile(self.cfg_file):
            os.rename(self.cfg_file, os.path.join(os.path.dirname(self.cfg_file), '.'+os.path.basename(self.cfg_file)+'~'))
        with open(self.cfg_file, 'wt') as f:
            f.write(yaml.dump(tree, sort_keys=False))
        self.edited = False
        self.but_save.Disable()


# ##########################################################################
# # class DictPanel
# # Base class for the outputs and filters ABMs
# ##########################################################################

class DictPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        # All the widgets
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        #  List box + buttons
        abm_sizer = wx.BoxSizer(wx.HORIZONTAL)
        #   List box
        list_sizer = wx.BoxSizer(wx.VERTICAL)
        self.lbox = wx.ListBox(self, choices=[], style=wx.LB_SINGLE)
        self.refresh_lbox()
        list_sizer.Add(self.lbox, gh.SIZER_FLAGS_1)
        abm_sizer.Add(list_sizer, gh.SIZER_FLAGS_1_NO_BORDER)
        #   Buttons at the right
        abm_sizer.Add(add_abm_buttons(self), gh.SIZER_FLAGS_0_NO_EXPAND)
        main_sizer.Add(abm_sizer, gh.SIZER_FLAGS_1_NO_BORDER)

        self.SetSizer(main_sizer)
        self.Layout()

        # Connect Events
        self.lbox.Bind(wx.EVT_LISTBOX_DCLICK, self.OnItemDClick)
        self.but_up.Bind(wx.EVT_BUTTON, self.OnUp)
        self.but_down.Bind(wx.EVT_BUTTON, self.OnDown)
        self.but_add.Bind(wx.EVT_BUTTON, self.OnAdd)
        self.but_remove.Bind(wx.EVT_BUTTON, self.OnRemove)

    def mark_edited(self):
        self.Parent.Parent.mark_edited()

    def OnItemDClick(self, event):
        index, string, obj = get_selection(self.lbox)
        if obj is None:
            return False
        self.editing = obj
        self.pre_edit(obj)
        if edit_dict(self, obj, None, None, title=self.dict_type.capitalize()+" "+str(obj), validator=self.validate):
            self.mark_edited()
            self.lbox.SetString(index, str(obj))
            return True
        return False

    def pre_edit(self, obj):
        pass

    def validate(self, obj):
        if not obj.name:
            pop_error('You must provide a name for the '+self.dict_type)
            return False
        same_name = next((o for o in get_client_data(self.lbox) if o.name == obj.name), None)
        if same_name is not None and same_name != self.editing:
            pop_error(f'The `{obj.name}` name is already used by {same_name}')
            return False
        return True

    def OnUp(self, event):
        move_sel_up(self.lbox)
        self.mark_edited()

    def OnDown(self, event):
        move_sel_down(self.lbox)
        self.mark_edited()

    def OnAdd(self, event):
        kind = self.choose_type()
        if kind is None:
            return
        # Create a new object of the selected type
        self.editing = obj = self.new_obj(kind)
        if edit_dict(self, obj, None, None, title=f"New {kind} filter", validator=self.validate):
            self.lbox.Append(str(obj), obj)
            self.mark_edited()

    def OnRemove(self, event):
        if remove_item(self.lbox, confirm='Are you sure you want to remove the `{}` '+self.dict_type+'?'):
            self.mark_edited()


# ##########################################################################
# # Class OutputsPanel
# # Panel containing the outputs ABM
# ##########################################################################

class OutputsPanel(DictPanel):
    def __init__(self, parent, outputs):
        self.outputs = outputs
        super().__init__(parent)
        self.dict_type = "output"

    def refresh_lbox(self):
        set_items(self.lbox, self.outputs)   # Populate the listbox

    def pre_edit(self, obj):
        self.grps_before = set(obj.groups)

    def OnItemDClick(self, event):
        if super().OnItemDClick(event):
            obj = self.editing
            # Adjust the groups involved
            grps_after = set(obj.groups)
            changed = False
            # - Added
            for g in grps_after-self.grps_before:
                RegOutput.add_out_to_group(obj, g)
                changed = True
            # - Removed
            for g in self.grps_before-grps_after:
                RegOutput.remove_out_from_group(obj, g)
                changed = True
            if changed:
                self.Parent.Parent.refresh_groups()

    def choose_type(self):
        return choose_from_list(self, list(RegOutput.get_registered().keys()), 'an output type')

    def new_obj(self, kind):
        # Create a new object of the selected type
        obj = RegOutput.get_class_for(kind)()
        obj.type = kind
        obj._tree = {}
        config_output(obj)
        return obj


# ##########################################################################
# # class GroupsPanel
# # Panel containing the groups ABM
# ##########################################################################

class GroupsPanel(wx.Panel):
    def __init__(self, parent, outputs):
        wx.Panel.__init__(self, parent)
        self.outputs = outputs

        # All the widgets
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        #  List box + buttons
        abm_sizer = wx.BoxSizer(wx.HORIZONTAL)
        #   List box
        list_sizer = wx.BoxSizer(wx.VERTICAL)
        self.lbox = wx.ListBox(self, choices=[], style=wx.LB_SINGLE)
        self.refresh_groups()
        list_sizer.Add(self.lbox, gh.SIZER_FLAGS_1)
        abm_sizer.Add(list_sizer, gh.SIZER_FLAGS_1_NO_BORDER)
        #   Buttons at the right
        abm_sizer.Add(add_abm_buttons(self), gh.SIZER_FLAGS_0_NO_EXPAND)
        main_sizer.Add(abm_sizer, gh.SIZER_FLAGS_1_NO_BORDER)

        self.SetSizer(main_sizer)
        self.Layout()

        # Connect Events
        self.lbox.Bind(wx.EVT_LISTBOX_DCLICK, self.OnItemDClick)
        self.but_up.Bind(wx.EVT_BUTTON, self.OnUp)
        self.but_down.Bind(wx.EVT_BUTTON, self.OnDown)
        self.but_add.Bind(wx.EVT_BUTTON, self.OnAdd)
        self.but_remove.Bind(wx.EVT_BUTTON, self.OnRemove)

    def refresh_groups(self):
        groups = list(RegOutput.get_groups_struct().values())
        for g in groups:
            g.update_out()
        set_items(self.lbox, groups)

    def mark_edited(self):
        self.Parent.Parent.mark_edited()

    def edit_group(self, group, is_new=False):
        group_names = [g.name for g in get_client_data(self.lbox)]
        used_names = set(group_names+[o.name for o in self.outputs])
        position = self.lbox.Selection
        if not is_new:
            del group_names[position]
        if not is_new:
            # Avoid messing with the actual group
            group = deepcopy(group)
        dlg = EditGroupDialog(self, group, self.outputs, used_names, group_names, is_new)
        res = dlg.ShowModal()
        if res == wx.ID_OK:
            new_name = dlg.name_text.Value
            lst_objs = get_client_data(dlg.lbox)
            if is_new:
                new_grp = RegOutput.add_group(new_name, lst_objs)
                self.lbox.Append(str(new_grp), new_grp)
            else:
                new_grp = RegOutput.replace_group(group.name, new_name, lst_objs)
                self.lbox.SetString(position, str(new_grp))
                self.lbox.SetClientData(position, new_grp)
            new_grp.update_out()
            self.mark_edited()
        dlg.Destroy()

    def OnItemDClick(self, event):
        self.edit_group(self.lbox.GetClientData(self.lbox.Selection))

    def OnUp(self, event):
        move_sel_up(self.lbox)
        self.mark_edited()

    def OnDown(self, event):
        move_sel_down(self.lbox)
        self.mark_edited()

    def OnAdd(self, event):
        self.edit_group(Group('new_group', []), is_new=True)

    def OnRemove(self, event):
        if remove_item(self.lbox, confirm='Are you sure you want to remove the `{}` group?'):
            self.mark_edited()


# ##########################################################################
# # class EditGroupDialog
# # Dialog to edit one group
# ##########################################################################

class EditGroupDialog(wx.Dialog):
    """ Edit a group, can be a new one """
    def __init__(self, parent, group, outputs, used_names, group_names, is_new):
        self.initialized = False
        wx.Dialog.__init__(self, parent, title="Add/Edit group",
                           style=wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP | wx.BORDER_DEFAULT)

        # All the widgets
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        #  Group name
        ttip = "Name for the group. Must be unique and different from any output."
        _, self.name_text, grp_name_sizer = input_label_and_text(self, "Group name", group.name, ttip, -1,
                                                                 style=wx.TE_PROCESS_ENTER)
        main_sizer.Add(grp_name_sizer, gh.SIZER_FLAGS_0_NO_BORDER)
        #  Static Box with the ABM
        sb_sizer = wx.StaticBoxSizer(wx.VERTICAL, self, "Outputs and groups")
        sb = sb_sizer.GetStaticBox()
        #   List box + buttons
        abm_sizer = wx.BoxSizer(wx.HORIZONTAL)
        #    List box
        list_sizer = wx.BoxSizer(wx.VERTICAL)
        self.lbox = wx.ListBox(sb, choices=[], style=wx.LB_SINGLE)
        self.lbox.SetToolTip("Outputs and groups that belongs to this group")
        set_items(self.lbox, group.items)   # Populate the listbox
        list_sizer.Add(self.lbox, gh.SIZER_FLAGS_1)
        abm_sizer.Add(list_sizer, gh.SIZER_FLAGS_1_NO_BORDER)
        #    Buttons at the right
        abm_buts = add_abm_buttons(self, sb, add_add=True, add_add_ttip="Add a group to this group",
                                   add_ttip="Add one or more outputs to the group")
        abm_sizer.Add(abm_buts, gh.SIZER_FLAGS_0_NO_EXPAND)
        sb_sizer.Add(abm_sizer, gh.SIZER_FLAGS_1_NO_BORDER)
        main_sizer.Add(sb_sizer, gh.SIZER_FLAGS_1)
        #  Status
        status_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.status_text = wx.StaticText(self, label="OK", style=wx.ST_NO_AUTORESIZE)
        status_sizer.Add(self.status_text, gh.SIZER_FLAGS_1)
        main_sizer.Add(status_sizer, gh.SIZER_FLAGS_0_NO_BORDER)
        #  OK/Cancel
        main_sizer.Add(ok_cancel(self), gh.SIZER_FLAGS_0)

        self.SetSizer(main_sizer)  # Size hints comes from the main_sizer
        main_sizer.Fit(self)       # Ask the main_sizer to make the dialog big enough
        self.Layout()
        self.Centre(wx.BOTH)

        # Connect Events
        self.Bind(wx.EVT_CHAR_HOOK, self.OnKey)
        self.name_text.Bind(wx.EVT_TEXT, self.ValidateName)
        self.lbox.Bind(wx.EVT_KEY_UP, self.OnKey)
        self.but_up.Bind(wx.EVT_BUTTON, self.OnUp)
        self.but_down.Bind(wx.EVT_BUTTON, self.OnDown)
        self.but_add.Bind(wx.EVT_BUTTON, self.OnAdd)
        self.but_add_add.Bind(wx.EVT_BUTTON, self.OnAddG)
        self.but_remove.Bind(wx.EVT_BUTTON, self.OnRemove)

        self.initialized = True

        self.used_names = used_names
        self.group_names = group_names
        self.valid_list = bool(len(group.items))
        self.is_new = is_new
        self.original_name = group.name
        self.input_is_normal = True
        self.normal_bkg = self.name_text.GetBackgroundColour()
        self.red = wx.Colour(0xFF, 0x40, 0x40)
        self.green = wx.Colour(0x40, 0xFF, 0x40)
        self.outputs = outputs

        self.status_text.SetForegroundColour(wx.Colour(0, 0, 0))
        self.valid_name = True
        self.ok = True
        self.status_txt = ''
        self.eval_status()

    def update_status(self):
        if self.ok:
            self.status_text.SetLabel(OK_CHAR+' '+self.status_txt)
            self.status_text.SetBackgroundColour(self.green)
            self.but_ok.Enable()
        else:
            self.status_text.SetLabel(NOT_OK_CHAR+' '+self.status_txt)
            self.status_text.SetBackgroundColour(self.red)
            self.but_ok.Disable()

    def set_status(self, ok, msg=None):
        if msg is None:
            msg = 'Ok'
        if ok == self.ok and msg == self.status_txt:
            return
        self.ok = ok
        self.status_txt = msg
        self.update_status()

    def eval_status(self):
        if not self.valid_name:
            self.set_status(False, 'name '+self.name_why)
        elif not self.valid_list:
            self.set_status(False, 'no outputs selected')
        else:
            self.set_status(True)

    def is_valid_name(self, name):
        if not name:
            return False, "is empty"
        if name[0] == '_':
            return False, "starts with underscore"
        if self.is_new:
            if name in self.used_names:
                return False, "already used"
            return True, None
        # Not new
        if name == self.original_name:
            # Same name
            return True, None
        if name in self.used_names:
            return False, "already used"
        return True, None

    def ValidateName(self, event):
        """ Called by the TextCtrl On Text """
        if not self.initialized:
            return
        cur_name = self.name_text.Value
        self.valid_name, self.name_why = self.is_valid_name(cur_name)
        self.eval_status()

    def OnKey(self, event):
        """ Called by the dialog OnCharHook and from the listbox OnKeyUp """
        if event.GetKeyCode() == wx.WXK_RETURN and self.valid_name and self.valid_list:
            self.EndModal(wx.ID_OK)
        else:
            # Not our key, continue processing it
            event.Skip()

    def OnUp(self, event):
        move_sel_up(self.lbox)

    def OnDown(self, event):
        move_sel_down(self.lbox)

    def OnAdd(self, event):
        selected = {i.out for i in get_client_data(self.lbox)}
        available = {str(o): o for o in self.outputs if o not in selected}
        available_names = [o.name for o in self.outputs if o not in selected]
        if not available:
            pop_error('No outputs available to add')
            return
        outs = choose_from_list(self, list(available.keys()), what="an output", multiple=True, search_on=available_names)
        if not outs:
            return
        for out in outs:
            o = available[out]
            i = GroupEntry(o.name, out=o)
            self.lbox.Append(str(i), i)
        self.valid_list = True
        self.eval_status()

    def OnAddG(self, event):
        if not self.group_names:
            pop_error('No groups available to add')
            return
        groups = choose_from_list(self, self.group_names, what='a group', multiple=True)
        if not groups:
            return
        for g in groups:
            i = GroupEntry(g)
            self.lbox.Append(str(i), i)
        self.valid_list = True
        self.eval_status()

    def OnRemove(self, event):
        index, string, obj = get_selection(self.lbox)
        if obj is None:
            # Nested group, can be only from the top-level definition
            return
        # Not defined in "groups" section
        if not obj.is_from_top():
            pop_info('This entry is from the `groups` option.\nRemove it from the output')
            return
        # Also defined in an output
        if obj.is_from_output():
            # Also defined in an output
            obj.from_top = False
            pop_info('This entry was also defined in the `groups` option.\nNow removed from the `groups` section.')
            self.lbox.SetString(index, str(obj))
            return
        remove_item(self.lbox)
        self.valid_list = bool(self.lbox.GetCount())
        self.eval_status()


# ##########################################################################
# # class FiltersPanel
# # Panel containing the filters ABM
# ##########################################################################

class FiltersPanel(DictPanel):
    def __init__(self, parent):
        super().__init__(parent)
        self.dict_type = "filter"

    def refresh_lbox(self):
        set_items(self.lbox, [f for f in RegOutput.get_filters().values() if not f.name.startswith('_')])

    def choose_type(self):
        return choose_from_list(self, list(RegFilter.get_registered().keys()), 'a filter type')

    def new_obj(self, kind):
        # Create a new object of the selected type
        obj = RegFilter.get_class_for(kind)()
        obj.type = kind
        obj._tree = {'name': 'new_filter'}
        obj.config(None)
        return obj
