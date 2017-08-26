#!/usr/bin/python

import wx
import threading
import time

def MapAllWithProgress(elems, f, title="Working"):
    dlg = wx.ProgressDialog(title, "", len(elems),
	                    style=wx.PD_APP_MODAL|wx.PD_AUTO_HIDE|wx.PD_REMAINING_TIME)
    cancelled = threading.Event()
    dlg.Bind(wx.EVT_CLOSE, lambda _: cancelled.set())
    def map_in_other_thread(elems, dlg):
	    for (i, e) in enumerate(elems):
		if cancelled.is_set() or dlg.WasCancelled():
		    break

		wx.CallAfter(dlg.Update, i, str(e))
		f(e)
	    wx.CallAfter(dlg.EndModal, 0)

    thd = threading.Thread(target=map_in_other_thread, args=(elems, dlg))
    thd.daemon = True
    thd.start()
    dlg.ShowModal()

class Downloader(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(Downloader, self).__init__(*args, **kwargs)

        panel = wx.Panel(self, wx.ID_ANY)
        self.button = wx.Button(panel, label="Start")
        self.button.Bind(wx.EVT_BUTTON, self.onButton)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.button, 0, wx.ALL|wx.CENTER, 5)
        panel.SetSizer(sizer)

    def onButton(self, event):
	button = event.GetEventObject()
        button.Disable()

        elems = map(str, range(15))
        try:
	    MapAllWithProgress(elems, lambda _: time.sleep(1))
	finally:
	    button.Enable()
        

app = wx.App()
d = Downloader(None, title="TED Downloader")
d.Show()
app.MainLoop()
