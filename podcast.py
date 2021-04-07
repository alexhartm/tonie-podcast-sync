#! /usr/bin/env python3
from bs4 import BeautifulSoup
import requests
import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

class Podcast:
    def __init__(self, url):
        self.url = url  # feed url of podcast 
        self.title = self.__getTitle() # title of podcast
        self.epList = [] # a list of all episodes
        self.refreshFeed() # reads feed and populates the episode list

    def __getTitle(self):
    # extract title of podcast from feed
        try:
            r = requests.get(self.url)
            soup = BeautifulSoup(r.content, features='xml')
            return soup.find('title').text        
        except Exception as e:
            log.error(f'failed reading podcast name: %e', e)
            return ""

    def refreshFeed(self):
    # reads feed and populates the episode list
        try:
            r = requests.get(self.url)
            soup = BeautifulSoup(r.content, features='xml')
            items = soup.findAll('item')        
            for i in items:
                _t = i.find('title').text
                _url = i.find('enclosure').attrs['url']
                _pd = i.find('pubDate').text 
                _dur = i.find('duration').text
                _guid = i.find('guid').text
                eObj = Episode(self.title, _t, _url, _pd, _dur, _guid)
                self.epList.append(eObj)
            log.info(f'%s: feed refreshed, %s episodes found.', self.title, len(items) )
        except Exception as e:
            log.error(f'%s: feed scraping failed: %s', self.title, e)

class Episode:
    def __init__(self, podcast, title, url, date, durationStr, guid):
        self.podcast = podcast          # Podcast Title this episode belongs to 
        self.title = title              # title
        self.date = date                # date when published (string)
        self.url = url                  # url of audio file
        self.guid = guid                # GUID
        self.fname = ""                 # filename for disk storage
        self.fpath = ""                 # path for disk storage
        self.durationStr = durationStr  # duration string as in feed
        self.durationSec = self.__durStr2sec(durationStr) # ... in sec

    def __durStr2sec(self, str):
        h, m, s = str.split(':')
        return int(h) * 3600 + int(m) * 60 + int(s)