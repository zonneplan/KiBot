import os
import wx
from ..gs import GS
loaded_btns = {}


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


def input_label_and_text(parent, lbl, initial, help, txt_w, lbl_w=-1):
    sizer = wx.BoxSizer(wx.HORIZONTAL)
    label = wx.StaticText(parent, label=lbl, size=wx.Size(lbl_w, -1), style=wx.ALIGN_RIGHT)
    label.SetToolTip(help)
    input = wx.TextCtrl(parent, value=initial, size=wx.Size(txt_w, -1))
    input.SetToolTip(help)
    sizer.Add(label, 0, wx.EXPAND | wx.ALL, 5)
    sizer.Add(input, 1, wx.EXPAND | wx.ALL, 5)
    return input, sizer
