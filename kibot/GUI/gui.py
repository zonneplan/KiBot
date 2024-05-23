# https://github.com/wxFormBuilder/wxFormBuilder

import os
import yaml
from . import main_dialog_base
from .. import __version__
from .. import log
from ..kiplot import config_output
from ..registrable import RegOutput
from .data_types import edit_dict
from .gui_helpers import (move_sel_up, move_sel_down, remove_item, pop_error, get_client_data,
                          set_items, get_selection, init_vars, choose_from_list,
                          set_button_bitmap)
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


def set_best_size(self, ref):
    best_size = ref.BestSize
    # hack for some gtk themes that incorrectly calculate best size
    best_size.IncBy(dx=0, dy=30)
    self.SetClientSize(best_size)


class MainDialog(main_dialog_base.MainDialogBase):
    def __init__(self, outputs, cfg_file):
        main_dialog_base.MainDialogBase.__init__(self, None)
        self.panel = MainDialogPanel(self, outputs, cfg_file)
        set_best_size(self, self.panel)
        self.SetTitle('KiBot '+__version__)


def do_gui(outputs, cfg_file):
    for o in outputs:
        config_output(o)
    dlg = MainDialog(outputs, cfg_file)
    res = dlg.ShowModal()
    dlg.Destroy()
    return res


class MainDialogPanel(main_dialog_base.MainDialogPanel):
    def __init__(self, parent, outputs, cfg_file):
        main_dialog_base.MainDialogPanel.__init__(self, parent)

        self.outputs = OutputsPanel(self.notebook, outputs)
        self.groups = GroupsPanel(self.notebook, outputs)
        self.notebook.AddPage(self.outputs, "Outputs")
        self.notebook.AddPage(self.groups, "Groups")
        # TODO: Remove these panels used as examples
        # self.general = main_dialog_base.GeneralSettingsPanelBase(self.notebook)
        # self.html = main_dialog_base.HtmlSettingsPanelBase(self.notebook)
        # self.fields = main_dialog_base.FieldsPanelBase(self.notebook)
        # self.notebook.AddPage(self.general, "General")
        # self.notebook.AddPage(self.html, "Html defaults")
        # self.notebook.AddPage(self.fields, "Fields")
        self.cfg_file = cfg_file
        self.edited = False
        set_button_bitmap(self.saveConfigBtn, wx.ART_FILE_SAVE)
        self.saveConfigBtn.Disable()
        set_button_bitmap(self.generateOutputsBtn, wx.ART_EXECUTABLE_FILE)

    def mark_edited(self):
        if not self.edited:
            self.saveConfigBtn.Enable(True)
        self.edited = True

    def OnSave(self, event):
        tree = {'kibot': {'version': 1}, 'outputs': [o._tree for o in get_client_data(self.outputs.outputsBox)]}
        if os.path.isfile(self.cfg_file):
            os.rename(self.cfg_file, os.path.join(os.path.dirname(self.cfg_file), '.'+os.path.basename(self.cfg_file)+'~'))
        with open(self.cfg_file, 'wt') as f:
            f.write(yaml.dump(tree, sort_keys=False))
        self.edited = False
        self.saveConfigBtn.Disable()


class OutputsPanel(main_dialog_base.OutputsPanelBase):
    def __init__(self, parent, outputs):
        main_dialog_base.OutputsPanelBase.__init__(self, parent)
        # Set the bitmaps for the buttons
        set_button_bitmap(self.m_btnOutUp, wx.ART_GO_UP)
        set_button_bitmap(self.m_btnOutDown, wx.ART_GO_DOWN)
        set_button_bitmap(self.m_btnOutAdd, wx.ART_PLUS)
        set_button_bitmap(self.m_btnOutRemove, wx.ART_MINUS)
        # Populate the listbox
        set_items(self.outputsBox, outputs)
        self.Layout()

    def mark_edited(self):
        self.Parent.Parent.mark_edited()

    def OnItemDClick(self, event):
        index, string, obj = get_selection(self.outputsBox)
        if obj is None:
            return
        self.editing = obj
        if edit_dict(self, obj, None, None, title="Output "+str(obj), validator=self.validate):
            self.mark_edited()
            self.outputsBox.SetString(index, str(obj))

    def OnOutputsOrderUp(self, event):
        move_sel_up(self.outputsBox)
        self.mark_edited()

    def OnOutputsOrderDown(self, event):
        move_sel_down(self.outputsBox)
        self.mark_edited()

    def OnOutputsOrderAdd(self, event):
        kind = choose_from_list(self, list(RegOutput.get_registered().keys()), 'an output type')
        if kind is None:
            return
        # Create a new object of the selected type
        obj = RegOutput.get_class_for(kind)()
        obj.type = kind
        obj._tree = {}
        config_output(obj)
        if edit_dict(self, obj, None, None, title=f"New {kind} output", validator=self.validate):
            self.outputsBox.Append(str(obj), obj)
            self.mark_edited()

    def OnOutputsOrderRemove(self, event):
        remove_item(self.outputsBox, confirm='Are you sure you want to remove the `{}` output?')
        self.mark_edited()

    def validate(self, obj):
        if not obj.name:
            pop_error('You must provide a name for the output')
            return False
        same_name = next((out for out in get_client_data(self.outputsBox) if out.name == obj.name), None)
        if same_name is not None and same_name != self.editing:
            pop_error(f'The `{obj.name}` name is already used by {same_name}')
            return False
        return True


# ##########################################################################
# # Panel for the groups
# ##########################################################################

class GroupsPanel(main_dialog_base.GroupsPanelBase):
    def __init__(self, parent, outputs):
        main_dialog_base.GroupsPanelBase.__init__(self, parent)

        set_button_bitmap(self.m_btnGrUp, wx.ART_GO_UP)
        set_button_bitmap(self.m_btnGrDown, wx.ART_GO_DOWN)
        set_button_bitmap(self.m_btnGrAdd, wx.ART_PLUS)
        set_button_bitmap(self.m_btnGrRemove, wx.ART_MINUS)

        self.groupsBox.SetItems(list(RegOutput.get_group_names()))
        for n, g in enumerate(RegOutput.get_groups().values()):
            outs = []
            for name in g:
                out = RegOutput.get_output(name)
                if out is None:
                    # Can be another group
                    out = name
                outs.append(out)
            self.groupsBox.SetClientData(n, outs)
        self.outputs = outputs

        self.Layout()

    def edit_group(self, name, selected, is_new=False, position=None):
        group_names = self.groupsBox.GetItems()
        used_names = set(group_names+[o.name for o in self.outputs])
        if not is_new:
            del group_names[position]
        dlg = EditGroupDialog(self, name, selected, self.outputs, used_names, group_names, is_new)
        res = dlg.ShowModal()
        if res == wx.ID_OK:
            new_name = dlg.nameText.Value
            lst_objs = get_client_data(dlg.outputsBox)
            lst_names = [o if isinstance(o, str) else o.name for o in lst_objs]
            if is_new:
                RegOutput.add_group(new_name, lst_names)
                self.groupsBox.Append(new_name, lst_objs)
            else:
                RegOutput.replace_group(name, new_name, lst_names)
                self.groupsBox.SetString(position, new_name)
                self.groupsBox.SetClientData(position, lst_objs)
        dlg.Destroy()

    def OnItemDClick(self, event):
        position = self.groupsBox.Selection
        item = self.groupsBox.GetString(position)
        outs = self.groupsBox.GetClientData(position)
        self.edit_group(item, outs, position=position)

    def OnGroupsOrderUp(self, event):
        move_sel_up(self.groupsBox)

    def OnGroupsOrderDown(self, event):
        move_sel_down(self.groupsBox)

    def OnGroupsOrderAdd(self, event):
        self.edit_group('new_group', [], is_new=True)

    def OnGroupsOrderRemove(self, event):
        remove_item(self.groupsBox, confirm='Are you sure you want to remove the `{}` group?')


# ##########################################################################
# # Dialog to edit one group
# ##########################################################################

class EditGroupDialog(main_dialog_base.AddGroupDialogBase):
    """ Edit a group, can be a new one """
    def __init__(self, parent, name, selected, outputs, used_names, group_names, is_new):
        self.initialized = False
        main_dialog_base.AddGroupDialogBase.__init__(self, parent)
        self.initialized = True

        set_button_bitmap(self.m_btnOutUp, wx.ART_GO_UP)
        set_button_bitmap(self.m_btnOutDown, wx.ART_GO_DOWN)
        set_button_bitmap(self.m_btnOutAdd, wx.ART_PLUS)
        set_button_bitmap(self.m_btnOutAddG, wx.ART_LIST_VIEW)
        set_button_bitmap(self.m_btnOutRemove, wx.ART_MINUS)

        set_items(self.outputsBox, selected)
        self.used_names = used_names
        self.group_names = group_names
        self.valid_list = bool(len(selected))
        self.is_new = is_new
        self.original_name = name
        self.input_is_normal = True
        self.normal_bkg = self.nameText.GetBackgroundColour()
        self.red = wx.Colour(0xFF, 0x40, 0x40)
        self.green = wx.Colour(0x40, 0xFF, 0x40)
        self.outputs = outputs

        self.m_Status.SetForegroundColour(wx.Colour(0, 0, 0))
        self.valid_name = True
        self.ok = True
        self.status_txt = ''
        self.eval_status()

        self.nameText.Value = name

        self.Layout()

    def update_status(self):
        if self.ok:
            self.m_Status.SetLabel(OK_CHAR+' '+self.status_txt)
            self.m_Status.SetBackgroundColour(self.green)
            self.m_butsOK.Enable()
        else:
            self.m_Status.SetLabel(NOT_OK_CHAR+' '+self.status_txt)
            self.m_Status.SetBackgroundColour(self.red)
            self.m_butsOK.Disable()

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
        cur_name = self.nameText.Value
        self.valid_name, self.name_why = self.is_valid_name(cur_name)
        self.eval_status()

    def OnKey(self, event):
        """ Called by the dialog OnCharHook and from the listbox OnKeyUp """
        if event.GetKeyCode() == wx.WXK_RETURN and self.valid_name and self.valid_list:
            self.EndModal(wx.ID_OK)
        else:
            # Not our key, continue processing it
            event.Skip()

    def OnOutputsOrderUp(self, event):
        move_sel_up(self.outputsBox)

    def OnOutputsOrderDown(self, event):
        move_sel_down(self.outputsBox)

    def OnOutputsOrderAdd(self, event):
        selected = set(get_client_data(self.outputsBox))
        available = {str(o): o for o in self.outputs if o not in selected}
        available_names = [o.name for o in self.outputs if o not in selected]
        if not available:
            pop_error('No outputs available to add')
            return
        outs = choose_from_list(self, list(available.keys()), what="an output", multiple=True, search_on=available_names)
        if not outs:
            return
        for out in outs:
            self.outputsBox.Append(out, available[out])
        self.valid_list = True
        self.eval_status()

    def OnOutputsOrderAddG(self, event):
        if not self.group_names:
            pop_error('No groups available to add')
            return
        groups = choose_from_list(self, self.group_names, what='a group', multiple=True)
        if not groups:
            return
        for g in groups:
            self.outputsBox.Append(g, g)
        self.valid_list = True
        self.eval_status()

    def OnOutputsOrderRemove(self, event):
        remove_item(self.outputsBox)
        self.valid_list = bool(self.outputsBox.GetCount())
        self.eval_status()
