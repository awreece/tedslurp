#!/usr/bin/env python

import json
import re
import requests
from bs4 import BeautifulSoup
import argparse
import textwrap
import time
from urllib.parse import urlparse
import os
import logging

def link_stream(attr="sort=popular&topics%5B%5D=Science&language=en", start=1, count=1):
    i = start
    while i < start + count:
        r = requests.get("https://www.ted.com/talks?page=%d&%s" % (i, attr))
        soup = BeautifulSoup(r.text, "html.parser")
        mylinks = soup.select(".talk-link .media__message a")
        for l in mylinks:
            yield l['href']
        i = i + 1

def get_audio_link(link):
    regex = re.compile("\"__INITIAL_DATA__\": (.*)\n")
    r = requests.get("https://www.ted.com" + link)
    data = regex.search(r.text).groups()[0]
    j = json.loads(data)
    print(j['media']['internal']['audio-podcast']['uri'])
    return j['media']['internal']['audio-podcast']['uri']
    
parser = argparse.ArgumentParser()
parser.add_argument("--sleep", default=2.0, type=float, help="How long to sleep between requests")
parser.add_argument("--start", default=1, type=int, help="Which page to start from")
parser.add_argument("--filter", default="sort=popular&topics%5B%5D=Science&language=en")
parser.add_argument("--count", default=1, type=int, help="How many pages to download")

args = parser.parse_args()

for link in link_stream(args.filter, start=args.start, count=args.count):
    time.sleep(args.sleep)
    path = None
    try:
        audio_link = get_audio_link(link)
        r = requests.get(audio_link, stream=True)
        path = urlparse(audio_link).path[1:]

        if os.path.exists(path):
            continue
        with open(path, "wb") as f:
            for data in r.iter_content(None):
                f.write(data)
    except:
        logging.exception("Failed to download " + link)
        if path:
            try:
                os.remove(path)
            except OSError:
                pass
        continue
