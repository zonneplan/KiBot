import os
import wx
from ..gs import GS
from . import gui_config
loaded_btns = {}
emp_font = None
sizer_flags_0 = sizer_flags_1 = sizer_flags_0_no_border = sizer_flags_1_no_border = None
sizer_flags_0_no_expand = sizer_flags_1_no_expand = None
USER_EDITED_COLOR = None


def init_vars():
    global emp_font, sizer_flags_0, sizer_flags_1, sizer_flags_0_no_border, sizer_flags_1_no_border, sizer_flags_0_no_expand
    global sizer_flags_1_no_expand, USER_EDITED_COLOR
    emp_font = wx.Font(70, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, True)
    sizer_flags_0 = wx.SizerFlags().Expand().Border(wx.ALL).CentreVertical()
    sizer_flags_1 = wx.SizerFlags(1).Expand().Border(wx.ALL).CentreVertical()
    sizer_flags_0_no_expand = wx.SizerFlags().Border(wx.ALL).CentreVertical()
    sizer_flags_1_no_expand = wx.SizerFlags(1).Border(wx.ALL).CentreVertical()
    sizer_flags_0_no_border = wx.SizerFlags().Expand().CentreVertical()
    sizer_flags_1_no_border = wx.SizerFlags(1).Expand().CentreVertical()
    USER_EDITED_COLOR = wx.Colour(gui_config.USER_EDITED_COLOR)


def _get_btn_bitmap(bitmap):
    path = os.path.join(GS.get_resource_path('images'), 'buttons', bitmap)
    png = wx.Bitmap(path, wx.BITMAP_TYPE_PNG)
    return wx.BitmapBundle(png)


def get_btn_bitmap(name):
    bitmap = 'btn-'+name+'.png'
    bmp = loaded_btns.get(bitmap, None)
    if bmp is None:
        bmp = _get_btn_bitmap(bitmap)
        loaded_btns[bitmap] = bmp
    return bmp


def pop_error(msg):
    wx.MessageBox(msg, 'Error', wx.OK | wx.ICON_ERROR)


def pop_confirm(msg):
    return wx.MessageBox(msg, 'Confirm', wx.YES_NO | wx.CANCEL | wx.CANCEL_DEFAULT | wx.ICON_QUESTION) == wx.YES


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


def ok_cancel(parent):
    m_but_sizer = wx.StdDialogButtonSizer()
    m_but_sizer.AddButton(wx.Button(parent, wx.ID_OK))
    m_but_sizer.AddButton(wx.Button(parent, wx.ID_CANCEL))
    m_but_sizer.Realize()
    return m_but_sizer


def get_emp_font():
    return emp_font


# def get_deemp_font():
#     global deemp_font
#     if deemp_font is None:
#         deemp_font = wx.Font(70, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL, False)
#     return deemp_font


def input_label_and_text(parent, lbl, initial, help, txt_w, lbl_w=-1):
    sizer = wx.BoxSizer(wx.HORIZONTAL)
    label = wx.StaticText(parent, label=lbl, size=wx.Size(lbl_w, -1), style=wx.ALIGN_RIGHT)
    label.SetToolTip(help)
    input = wx.TextCtrl(parent, value=initial, size=wx.Size(txt_w, -1))
    input.SetToolTip(help)
    sizer.Add(label, get_sizer_flags_0())
    sizer.Add(input, get_sizer_flags_1())
    return label, input, sizer


def get_client_data(container):
    return [container.GetClientData(n) for n in range(container.GetCount())]


def set_items(lbox, objs):
    """ Set the list box items using the string representation of the objs.
        Keep the objects in the client data """
    lbox.SetItems([str(o) for o in objs])
    for n, o in enumerate(objs):
        lbox.SetClientData(n, o)


def get_selection(lbox):
    """ Helper to get the current index, string and data for a list box selection """
    index = lbox.Selection
    if index == wx.NOT_FOUND:
        return index, None, None
    return index, lbox.GetString(index), lbox.GetClientData(index)


def get_sizer_flags_0():
    return sizer_flags_0


def get_sizer_flags_1():
    return sizer_flags_1


def get_sizer_flags_0_no_expand():
    return sizer_flags_0_no_expand


def get_sizer_flags_1_no_expand():
    return sizer_flags_1_no_expand


def get_sizer_flags_0_no_border():
    return sizer_flags_0_no_border


def get_sizer_flags_1_no_border():
    return sizer_flags_1_no_border
