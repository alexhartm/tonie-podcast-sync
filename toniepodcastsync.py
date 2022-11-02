#! /usr/bin/env python3
from podcast import Podcast
import sys, os, shutil, logging
import wget

from tonie_api.tonie_api import TonieAPI

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

class ToniePodcastSync:
    def __init__(self, user, pwd):
        self.__user = user
        self.__pwd = pwd
        self.__api=TonieAPI(user, pwd)
        self.__tonieDict = self.__refreshTonieDict() # tonies + households

    def printToniesOverview(self):
        print("List of available creative tonies:")
        for t in self.__tonieDict:
            print("   tonie ID " + t + " with name " + self.__api.households[self.__tonieDict[t]].creativetonies[t].name)

    def syncPodcast2Tonie(self, podcast, tonie, maxMin = 90):
    # sync new episodes from podcast feed to creative tonie
    # - this is done by wiping the tonie and writing all new episodes
    # limit episodes on tonie to maxMin minutes in total
    # return if no new episodes in feed
        if not tonie in self.__tonieDict:
            log.error(f'%s: cant find tonie', tonie)
            print("error: tried, but cant find tonie with ID " + tonie)
            return
        if len(podcast.epList) == 0:
            log.warn(f'%s: cant find any epsiodes at all', podcast.title)
            print(podcast.title + ": cant find any epsiodes at all, feed is empty")
            return
        if self.__isTonieEmpty(tonie) == False:    
            # check if new feed has newer epsiodes than tonie
            latestEpFeed = self.__generateChapterTitle(podcast.epList[0])
            latestEpTonie = self.__getFirstChapterOnTonie(tonie)["title"]
            if (latestEpTonie == latestEpFeed):
                log.info(f'%s: no new podcast epsiodes, latest episode is %s', podcast.title, latestEpTonie)
                print(podcast.title + ": no new podcast epsiodes, latest is \"" + latestEpTonie + "\"")
                return
        else:
            log.info(f'### tonie is empty')
        # add new episodes to tonie
        self.__wipeTonie(tonie)
        print(podcast.title + ": fetching new episodes...")
        cachedEps = self.__cachePodcastUpTo(podcast, maxMin)
        print(podcast.title + ": transferring " + str(len(cachedEps)) + " episodes to "+ self.__api.households[self.__tonieDict[tonie]].creativetonies[tonie].name)
        for e in cachedEps:
            self.__uploadEpisode(e, tonie)
            print(podcast.title + ": uploaded \"" + e.title + "\" (from " + e.date + ")")
        self.__cleanupCache(podcast)

    def __refreshTonieDict(self):
    # returns a dictionary with mapping tonies to households
        tonieDict = {}
        _hhL = self.__api.households_update()
        for _hh in _hhL:
            _tL = self.__api.households[_hh].creativetonies_update()
            for _t in _tL:
                log.info(f'found creative tonie %s in household %s', _t, _hh)
                tonieDict[_t] = _hh
        return tonieDict

    def __uploadEpisode(self, ep, tonie):
    # upload a given episode to a creative tonie
        hh = self.__tonieDict[tonie]
        f = os.path.join(ep.fpath, ep.fname)
        return self.__api.households[hh].creativetonies[tonie].upload(f, self.__generateChapterTitle(ep))

    def __wipeTonie(self, tonie):
    # delete all content on a tonie
        hh = self.__tonieDict[tonie]
        return self.__api.households[hh].creativetonies[tonie].remove_all_chapters()


    def __cachePodcastUpTo(self, podcast, maxMin = 90):
    # local download of all episodes of a podcast, limited to maxMin minutes in total
        if maxMin == 0: maxMin = 90 # default to 90 minutes
        if maxMin > 90: maxMin = 90 # tonies can't carry more than 90 minutes
        
        __totalSeconds = 0
        __no = 0
        epList = []

        for ep in podcast.epList:
            if (maxMin > 0) and ((__totalSeconds + ep.durationSec) >= (maxMin * 60)):
                log.info(f'%s: providing %s episodes with %d.1 min total', podcast.title, __no, (__totalSeconds / 60))
                return epList
            else:
                __no += 1
                __totalSeconds += ep.durationSec
                self.__cacheEpisode(ep)
                epList.append(ep)    
        log.info(f'%s: providing all %s episodes with %d.1 min total', podcast.title, __no, (__totalSeconds/60))
        return epList

    def __cacheEpisode(self, ep):
    # local download of a single episode into a subfolder
    # file name is build according to __generateFilename
        path = self.__generatePath(ep.podcast)
        # check if directory exists
        try:
            if not os.path.exists(path):
                log.info(f'directory %s created: ', path)
                os.makedirs(path)
        except Exception as e:
            log.error(f'dir %s failed to create: %s', path, e)
            return False   
        
        fname = self.__generateFilename(ep)
        # check if file exists already
        if os.path.exists( os.path.join(path, fname)):
            log.info(f'file %s exists already, will be overwritten', ep.guid)
            try:
                os.remove(os.path.join(path, fname))
            except Exception as e:
                log.error(f'file %s already existing, but failed to overwrite: %s', ep.guid, e)
        
        # the download part
        try:
            wget.download(ep.url, out = os.path.join(path, fname), bar=None)
            ep.fpath = path
            ep.fname = fname
            return True
        except Exception as e:
           log.error(f'%s writing to disk failed: %s', ep.guid, e)
           return False

    def __generateFilename(self, ep):
    # generates canonical filename for local episode cache
        fname = ep.date + " " + ep.title
        if fname[-4] != ".mp3": fname = fname + ".mp3"
        return fname

    def __generatePath(self, podcastTitle):
    # generates canonical path for local episode cache
        path = os.path.join("podcasts", podcastTitle)
        return path

    def __cleanupCache(self, podcast):
    # delete all cached files and folders from local storage
        path = self.__generatePath(podcast.title)
        log.info(f'cleaning up directory %s...', path)
        shutil.rmtree(path)
        if os.path.exists("podcasts") and os.path.isdir("podcasts") and not os.listdir("podcasts"):
            log.info(f'cleaning up directory %s...', "podcasts")
            shutil.rmtree("podcasts")

    def __generateChapterTitle(self, ep):
    # generate chapter title used when writing on tonie 
        return ep.title + " (" + ep.date + ")"

    def __getFirstChapterOnTonie(self, tonie):
    # returns the first chapter on tonie
        hh = self.__tonieDict[tonie]
        first = self.__api.households[hh].creativetonies[tonie].chapters[0]
        return first
 
    def __getChapterOnTonie(self, tonie, chapterPos):
    # returns chapter at chapterPos on tonie
        hh = self.__tonieDict[tonie]
        return self.__api.households[hh].creativetonies[tonie].chapters[chapterPos]

    def __isTonieEmpty(self, tonie):
        hh = self.__tonieDict[tonie]
        if len(self.__api.households[hh].creativetonies[tonie].chapters) == 0: 
            return True
        else: 
            return False