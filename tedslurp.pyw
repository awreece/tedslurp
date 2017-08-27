#!/usr/bin/python

import wx
import threading
import time
import requests
from bs4 import BeautifulSoup
import traceback
import logging
import re
import json
import os
from urllib.parse import urlparse

def MapAllWithProgress(elems, f, title="Working"):
    with wx.ProgressDialog(title, "", len(elems),
            style=wx.PD_APP_MODAL|wx.PD_AUTO_HIDE|wx.PD_REMAINING_TIME) as dlg:
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
        thd.join()

def Warn(parent, message):
    with wx.MessageDialog(parent, message, caption="Warning!",
                          style=wx.OK|wx.ICON_WARNING) as dlg:
        dlg.ShowModal()

def GetLinks(filter, page):
        r = requests.get("https://www.ted.com/talks?page=%d&%s" % (page, filter))
        soup = BeautifulSoup(r.text, "html.parser")
        mylinks = soup.select(".talk-link .media__message a")
        return [l["href"] for l in mylinks]


def get_audio_link(link):
    regex = re.compile("\"__INITIAL_DATA__\": (.*)\n")
    r = requests.get("https://www.ted.com" + link)
    data = regex.search(r.text).groups()[0]
    j = json.loads(data)
    return j['media']['internal']['audio-podcast']['uri']

def download(link, odir):
    time.sleep(1)
    path = None
    try:
        audio_link = get_audio_link(link)
        r = requests.get(audio_link, stream=True)
        path = os.path.join(odir, os.path.basename(urlparse(audio_link).path[1:]))

        if os.path.exists(path):
            logging.warning("%s already existed", path)
        with open(path, "wb") as f:
            for data in r.iter_content(None):
                f.write(data)
    except:
        logging.exception("Failed to download " + link)
        if path:
            try:
                os.remove(path)
            except OSError:
                raise

class Downloader(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(Downloader, self).__init__(*args, **kwargs)

        panel = wx.Panel(self, wx.ID_ANY)

        self.odirctrl = wx.DirPickerCtrl(panel, wx.ID_ANY, style=wx.DIRP_USE_TEXTCTRL)
        odirsizer = wx.BoxSizer(wx.HORIZONTAL)
        odirsizer.Add(wx.StaticText(panel, wx.ID_ANY, "Output Directory"), 1, wx.ALL, 5)
        odirsizer.Add(self.odirctrl, 3, wx.ALL|wx.EXPAND, 5)

        self.filterctrl = wx.TextCtrl(panel, wx.ID_ANY, value="sort=popular&topics%5B%5D=Science&language=en", style=wx.TE_NOHIDESEL)
        filtersizer = wx.BoxSizer(wx.HORIZONTAL)
        filtersizer.Add(wx.StaticText(panel, wx.ID_ANY, "TED.com filter"), 1, wx.ALL, 5)
        filtersizer.Add(self.filterctrl, 3, wx.ALL|wx.EXPAND, 5)

        self.pagectrl = wx.SpinCtrl(panel, wx.ID_ANY, initial=1, min=1)
        pagesizer = wx.BoxSizer(wx.HORIZONTAL)
        pagesizer.Add(wx.StaticText(panel, wx.ID_ANY, "Page"), 1, wx.ALL, 5)
        pagesizer.Add(self.pagectrl, 3, wx.ALL|wx.EXPAND, 5)



        button = wx.Button(panel, label="Start")
        button.Bind(wx.EVT_BUTTON, self.onButton)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(filtersizer, 0, wx.ALL|wx.EXPAND)
        sizer.Add(pagesizer, 0, wx.ALL|wx.EXPAND)
        sizer.Add(odirsizer, 0, wx.ALL|wx.EXPAND)
        sizer.Add(button, 0, wx.ALL|wx.EXPAND)
        panel.SetSizerAndFit(sizer)

    def _onButton(self):
        filter = self.filterctrl.GetLineText(0)
        odir = self.odirctrl.GetPath()
        page = self.pagectrl.GetValue()

        if not odir:
            Warn(self, "No output directory set")
            return

        try:
            links = GetLinks(filter, page)
        except e:
                Warn(self, "Failed to get links for filter")
                traceback.print_exc()
                return

        MapAllWithProgress(links, lambda l: download(l, odir))

    def onButton(self, event):
        button = event.GetEventObject()
        button.Disable()

        try:
            self._onButton()
        finally:
            button.Enable()

        

app = wx.App()
d = Downloader(None, title="TED Downloader")
d.Show()
app.MainLoop()
