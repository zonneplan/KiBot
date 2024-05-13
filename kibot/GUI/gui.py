# https://github.com/wxFormBuilder/wxFormBuilder

from . import main_dialog_base
from .. import __version__
from .. import log
from ..kiplot import config_output
from ..registrable import RegOutput
from .data_types import get_data_type_tree, add_widgets
from .gui_helpers import get_btn_bitmap
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


def pop_error(msg):
    wx.MessageBox(msg, 'Error', wx.OK | wx.ICON_ERROR)


def pop_confirm(msg):
    return wx.MessageBox(msg, 'Confirm', wx.YES_NO | wx.CANCEL | wx.CANCEL_DEFAULT | wx.ICON_QUESTION) == wx.YES


def set_best_size(self, ref):
    best_size = ref.BestSize
    # hack for some gtk themes that incorrectly calculate best size
    best_size.IncBy(dx=0, dy=30)
    self.SetClientSize(best_size)


def get_client_data(container):
    return [container.GetClientData(n) for n in range(container.GetCount())]


class MainDialog(main_dialog_base.MainDialogBase):
    def __init__(self, outputs):
        main_dialog_base.MainDialogBase.__init__(self, None)
        self.panel = MainDialogPanel(self, outputs)
        set_best_size(self, self.panel)
        self.SetTitle('KiBot '+__version__)


def do_gui(outputs):
    for o in outputs:
        config_output(o, dry=True)
    dlg = MainDialog(outputs)
    res = dlg.ShowModal()
    dlg.Destroy()
    return res


class MainDialogPanel(main_dialog_base.MainDialogPanel):
    def __init__(self, parent, outputs):
        main_dialog_base.MainDialogPanel.__init__(self, parent)

        self.outputs = OutputsPanel(self.notebook, outputs)
        self.groups = GroupsPanel(self.notebook, outputs)
        self.general = main_dialog_base.GeneralSettingsPanelBase(self.notebook)
        self.html = main_dialog_base.HtmlSettingsPanelBase(self.notebook)
        self.fields = main_dialog_base.FieldsPanelBase(self.notebook)
        self.notebook.AddPage(self.outputs, "Outputs")
        self.notebook.AddPage(self.groups, "Groups")
        # TODO: Remove these panels used as examples
        # self.notebook.AddPage(self.general, "General")
        # self.notebook.AddPage(self.html, "Html defaults")
        # self.notebook.AddPage(self.fields, "Fields")


def move_sel_up(box):
    """ Helper to move the selection up """
    selection = box.Selection
    if selection != wx.NOT_FOUND and selection > 0:
        item = box.GetString(selection)
        box.Delete(selection)
        box.Insert(item, selection-1)
        box.SetSelection(selection-1)


def move_sel_down(box):
    """ Helper to move the selection down """
    selection = box.Selection
    size = box.Count
    if selection != wx.NOT_FOUND and selection < size-1:
        item = box.GetString(selection)
        box.Delete(selection)
        box.Insert(item, selection+1)
        box.SetSelection(selection+1)


def set_items_from_output_objs(lbox, outputs):
    """ Set the list box items using the string representation of the outputs.
        Keep the objects in the client data """
    lbox.SetItems([str(o) for o in outputs])
    for n, o in enumerate(outputs):
        lbox.SetClientData(n, o)


def get_selection(lbox):
    """ Helper to get the current index, string and data for a list box selection """
    index = lbox.Selection
    if index == wx.NOT_FOUND:
        return index, None, None
    return index, lbox.GetString(index), lbox.GetClientData(index)


def edit_output(parent, o):
    dlg = EditOutput(parent, o)
    res = dlg.ShowModal()
    if res == wx.ID_OK:
        dlg.get_values()
    dlg.Destroy()
    return res


class EditOutput(wx.Dialog):
    def __init__(self, parent, o):
        # Generated code
        wx.Dialog.__init__(self,
                           parent,
                           id=wx.ID_ANY,
                           title="Output "+str(o),
                           style=wx.STAY_ON_TOP | wx.BORDER_DEFAULT | wx.CAPTION)  # wx.RESIZE_BORDER
        self.parent = parent
        # Main sizer
        b_sizer = wx.BoxSizer(wx.VERTICAL)
        # Output widgets sizer
        middle_sizer = wx.BoxSizer(wx.HORIZONTAL)
        # This is the area for the output widgets
        self.scrollWindow = wx.ScrolledWindow(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.VSCROLL)
        self.scrollWindow.SetScrollRate(5, 5)

        # Main widgets area, scrollable
        self.scrl_sizer = wx.BoxSizer(wx.VERTICAL)
        self.data_type_tree = get_data_type_tree(o)
        add_widgets(o, self.data_type_tree, self.scrollWindow, self.scrl_sizer)
        self.scrollWindow.SetSizer(self.scrl_sizer)
        self.compute_scroll_hints()
        self.scrl_sizer.Fit(self.scrollWindow)
        self.scrollWindow.SetAutoLayout(True)
        middle_sizer.Add(self.scrollWindow, 1, wx.EXPAND | wx.ALL, 5)
        # Add the outputs are to the main sizer
        b_sizer.Add(middle_sizer, 1, wx.ALL | wx.EXPAND, 5)

        # Standard Ok/Cancel button
        m_but_sizer = wx.StdDialogButtonSizer()
        m_but_sizer.AddButton(wx.Button(self, wx.ID_OK))
        m_but_sizer.AddButton(wx.Button(self, wx.ID_CANCEL))
        m_but_sizer.Realize()
        b_sizer.Add(m_but_sizer, 0, wx.ALL | wx.EXPAND, 5)

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
            print(f'{entry.name} {entry.valids[0].get_value()}')

    def __del__(self):
        pass


class OutputsPanel(main_dialog_base.OutputsPanelBase):
    def __init__(self, parent, outputs):
        main_dialog_base.OutputsPanelBase.__init__(self, parent)
        # Set the bitmaps for the buttons
        self.m_btnOutUp.SetBitmap(get_btn_bitmap("arrow-up"))
        self.m_btnOutDown.SetBitmap(get_btn_bitmap("arrow-down"))
        self.m_btnOutAdd.SetBitmap(get_btn_bitmap("plus"))
        self.m_btnOutRemove.SetBitmap(get_btn_bitmap("minus"))
        # Populate the listbox
        set_items_from_output_objs(self.outputsBox, outputs)
        self.Layout()

    def OnItemDClick(self, event):
        index, string, obj = get_selection(self.outputsBox)
        if obj is None:
            return
        edit_output(self, obj)

    def OnOutputsOrderUp(self, event):
        move_sel_up(self.outputsBox)

    def OnOutputsOrderDown(self, event):
        move_sel_down(self.outputsBox)


def remove_item(lbox, confirm=None):
    selection = lbox.Selection
    if selection == wx.NOT_FOUND:
        return
    ok = True
    if confirm is not None:
        name = lbox.GetString(selection)
        msg = confirm.format(name)
        ok = pop_confirm(msg)
    if not ok:
        return
    lbox.Delete(selection)
    count = lbox.GetCount()
    lbox.SetSelection(min(selection, count-1))


# ##########################################################################
# # Panel for the groups
# ##########################################################################

class GroupsPanel(main_dialog_base.GroupsPanelBase):
    def __init__(self, parent, outputs):
        main_dialog_base.GroupsPanelBase.__init__(self, parent)

        self.m_btnGrUp.SetBitmap(get_btn_bitmap("arrow-up"))
        self.m_btnGrDown.SetBitmap(get_btn_bitmap("arrow-down"))
        self.m_btnGrAdd.SetBitmap(get_btn_bitmap("plus"))
        self.m_btnGrRemove.SetBitmap(get_btn_bitmap("minus"))

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
# # Helper to choose an item from a list
# # Used to choose one or more outputs or groups
# ##########################################################################

def choose_output(parent, available, what="an output", multiple=False):
    """ Create a dialog to choose an output from the `available` list
        Returns the index of the selected output or a list of if multiple enabled """
    dlg = ChooseOutput(parent, available, what, wx.LB_MULTIPLE if multiple else wx.LB_SINGLE)
    res = dlg.ShowModal()
    sel = (dlg.outputsBox.GetSelections() if multiple else dlg.outputsBox.Selection) if res == wx.ID_OK else None
    dlg.Destroy()
    return sel


class ChooseOutput(wx.Dialog):
    def __init__(self, parent, available, what, l_style=wx.LB_SINGLE):
        # Generated code
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title="Select "+what, pos=wx.DefaultPosition,
                           size=wx.Size(463, 529), style=wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP | wx.BORDER_DEFAULT)
        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)
        # Main sizer
        b_sizer = wx.BoxSizer(wx.VERTICAL)
        self.outputsBox = wx.ListBox(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, available, l_style)
        b_sizer.Add(self.outputsBox, 1, wx.ALL | wx.EXPAND, 5)
        # Standard Ok/Cancel
        m_but_sizer = wx.StdDialogButtonSizer()
        m_but_sizer.AddButton(wx.Button(self, wx.ID_OK))
        m_but_sizer.AddButton(wx.Button(self, wx.ID_CANCEL))
        m_but_sizer.Realize()
        b_sizer.Add(m_but_sizer, 0, wx.ALL | wx.EXPAND, 5)
        self.SetSizer(b_sizer)
        # Connect Events
        self.outputsBox.Bind(wx.EVT_LISTBOX_DCLICK, self.OnDClick)
        # Adjust the width to be optimal for the width of the outputs
        size = self.GetClientSize()
        lb_size = self.outputsBox.BestSize
        if lb_size.Width > size.Width:
            size.Width = lb_size.Width
            self.SetClientSize(size)
        # Done
        self.Layout()
        self.Centre(wx.BOTH)

    def __del__(self):
        pass

    def OnDClick(self, event):
        self.EndModal(wx.ID_OK)


# ##########################################################################
# # Dialog to edit one group
# ##########################################################################

class EditGroupDialog(main_dialog_base.AddGroupDialogBase):
    """ Edit a group, can be a new one """
    def __init__(self, parent, name, selected, outputs, used_names, group_names, is_new):
        self.initialized = False
        main_dialog_base.AddGroupDialogBase.__init__(self, parent)
        self.initialized = True

        self.m_btnOutUp.SetBitmap(get_btn_bitmap("arrow-up"))
        self.m_btnOutDown.SetBitmap(get_btn_bitmap("arrow-down"))
        self.m_btnOutAdd.SetBitmap(get_btn_bitmap("plus"))
        self.m_btnOutAddG.SetBitmap(get_btn_bitmap("plus-plus"))
        self.m_btnOutRemove.SetBitmap(get_btn_bitmap("minus"))

        set_items_from_output_objs(self.outputsBox, selected)
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
        available = [str(o) for o in self.outputs if o not in selected]
        if not available:
            pop_error('No outputs available to add')
            return
        outs = choose_output(self, available, multiple=True)
        if not outs:
            return
        available_o = [o for o in self.outputs if o not in selected]
        for out in outs:
            self.outputsBox.Append(available[out], available_o[out])
        self.valid_list = True
        self.eval_status()

    def OnOutputsOrderAddG(self, event):
        if not self.group_names:
            pop_error('No groups available to add')
            return
        groups = choose_output(self, self.group_names, 'a group', multiple=True)
        if not groups:
            return
        for g in groups:
            group = self.group_names[g]
            self.outputsBox.Append(group, group)
        self.valid_list = True
        self.eval_status()

    def OnOutputsOrderRemove(self, event):
        remove_item(self.outputsBox)
        self.valid_list = bool(self.outputsBox.GetCount())
        self.eval_status()
