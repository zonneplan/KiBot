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
