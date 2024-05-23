import difflib
import wx
from . import gui_config
# loaded_btns = {}
emp_font = None
SIZER_FLAGS_0 = SIZER_FLAGS_1 = SIZER_FLAGS_0_NO_BORDER = SIZER_FLAGS_1_NO_BORDER = None
SIZER_FLAGS_0_NO_EXPAND = SIZER_FLAGS_1_NO_EXPAND = None
USER_EDITED_COLOR = None


def init_vars():
    global emp_font, SIZER_FLAGS_0, SIZER_FLAGS_1, SIZER_FLAGS_0_NO_BORDER, SIZER_FLAGS_1_NO_BORDER, SIZER_FLAGS_0_NO_EXPAND
    global SIZER_FLAGS_1_NO_EXPAND, USER_EDITED_COLOR
    emp_font = wx.Font(70, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, True)
    SIZER_FLAGS_0 = wx.SizerFlags().Expand().Border(wx.ALL).CentreVertical()
    SIZER_FLAGS_1 = wx.SizerFlags(1).Expand().Border(wx.ALL).CentreVertical()
    SIZER_FLAGS_0_NO_EXPAND = wx.SizerFlags().Border(wx.ALL).CentreVertical()
    SIZER_FLAGS_1_NO_EXPAND = wx.SizerFlags(1).Border(wx.ALL).CentreVertical()
    SIZER_FLAGS_0_NO_BORDER = wx.SizerFlags().Expand().CentreVertical()
    SIZER_FLAGS_1_NO_BORDER = wx.SizerFlags(1).Expand().CentreVertical()
    USER_EDITED_COLOR = wx.Colour(gui_config.USER_EDITED_COLOR)


# def _get_btn_bitmap(bitmap):
#     path = os.path.join(GS.get_resource_path('images'), 'buttons', bitmap)
#     png = wx.Bitmap(path, wx.BITMAP_TYPE_PNG)
#     return wx.BitmapBundle(png)
#
#
# def get_btn_bitmap(name):
#     bitmap = 'btn-'+name+'.png'
#     bmp = loaded_btns.get(bitmap, None)
#     if bmp is None:
#         bmp = _get_btn_bitmap(bitmap)
#         loaded_btns[bitmap] = bmp
#     return bmp


def pop_error(msg):
    wx.MessageBox(msg, 'Error', wx.OK | wx.ICON_ERROR)


def pop_confirm(msg):
    # In wxGTK the Yes/No lacks icons, the Yes/No/Cancel is nicer
    return wx.MessageBox(msg, 'Confirm', wx.YES_NO | wx.CANCEL | wx.CANCEL_DEFAULT | wx.ICON_QUESTION) == wx.YES


def move_sel_up(box):
    """ Helper to move the selection up """
    selection = box.Selection
    if selection != wx.NOT_FOUND and selection > 0:
        item = box.GetString(selection)
        data = box.GetClientData(selection)
        box.Delete(selection)
        box.Insert(item, selection-1, data)
        box.SetSelection(selection-1)


def move_sel_down(box):
    """ Helper to move the selection down """
    selection = box.Selection
    size = box.Count
    if selection != wx.NOT_FOUND and selection < size-1:
        item = box.GetString(selection)
        data = box.GetClientData(selection)
        box.Delete(selection)
        box.Insert(item, selection+1, data)
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


def ok_cancel(parent, ok_callback=None):
    m_but_sizer = wx.StdDialogButtonSizer()
    btn_ok = wx.Button(parent, wx.ID_OK)
    m_but_sizer.AddButton(btn_ok)
    m_but_sizer.AddButton(wx.Button(parent, wx.ID_CANCEL))
    m_but_sizer.Realize()
    if ok_callback:
        btn_ok.Bind(wx.EVT_BUTTON, ok_callback)
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
    sizer.Add(label, SIZER_FLAGS_0)
    sizer.Add(input, SIZER_FLAGS_1)
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


class ChooseFromList(wx.Dialog):
    def __init__(self, parent, items, what, search, l_style, search_on):
        self.all_options = items
        self.search_on = search_on
        if search_on:
            self.translate = dict(zip(search_on, self.all_options))
        wx.Dialog.__init__(self, parent, title="Select "+what,
                           style=wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP | wx.BORDER_DEFAULT)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        if search:
            self.search = wx.SearchCtrl(self)
            main_sizer.Add(self.search, SIZER_FLAGS_0)
            self.search.Bind(wx.EVT_TEXT, self.OnText)
            # Take ENTER as a confirmation
            self.search.Bind(wx.EVT_SEARCH, self.OnDClick)
        self.lbox = wx.ListBox(self, choices=items, style=l_style)
        main_sizer.Add(self.lbox, SIZER_FLAGS_1)
        main_sizer.Add(ok_cancel(self), SIZER_FLAGS_0)
        self.SetSizer(main_sizer)
        main_sizer.SetSizeHints(self)
        self.lbox.Bind(wx.EVT_LISTBOX_DCLICK, self.OnDClick)
        # Adjust the width to be optimal for the width of the outputs
#         size = self.GetClientSize()
#         lb_size = self.lbox.BestSize
#         if lb_size.Width > size.Width:
#             size.Width = lb_size.Width
#             self.SetClientSize(size)
#         # Done
#         self.Layout()
#         self.Centre(wx.BOTH)

    def OnDClick(self, event):
        self.EndModal(wx.ID_OK)

    def OnText(self, event):
        text = event.GetString()
        options = self.search_on or self.all_options
        items = [o for o in options if o.startswith(text)]
        for s in difflib.get_close_matches(text, options, n=5, cutoff=0.3):
            if s not in items:
                items.append(s)
        if self.search_on:
            items = [self.translate[v] for v in items]
        self.lbox.SetItems(items)
        self.lbox.SetSelection(0)


def choose_from_list(parent, items, what, multiple=False, search_on=None):
    l_style = wx.LB_MULTIPLE if multiple else wx.LB_SINGLE
    dlg = ChooseFromList(parent, items, what, True, l_style, search_on)
    if dlg.ShowModal() == wx.ID_OK:
        if multiple:
            res = [dlg.lbox.GetString(i) for i in dlg.lbox.GetSelections()]
        else:
            res = dlg.lbox.GetString(dlg.lbox.Selection)
    else:
        res = None
    dlg.Destroy()
    return res


def get_res_bitmap(resource):
    return wx.BitmapBundle(wx.ArtProvider.GetBitmap(resource))


def set_button_bitmap(btn, resource):
    btn.SetBitmap(get_res_bitmap(resource))
