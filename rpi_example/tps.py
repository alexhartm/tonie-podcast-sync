#! /usr/bin/env python3
"""example python script for using tonie-podcast-sync."""
# ruff: noqa: ERA001

from toniepodcastsync import Podcast, ToniePodcastSync

maus = Podcast("https://kinder.wdr.de/radio/diemaus/audio/gute-nacht-mit-der-maus/diemaus-gute-nacht-104.podcast")
pumuckl = Podcast("https://feeds.br.de/pumuckl/feed.xml")
checkertobi = Podcast("https://feeds.br.de/checkpod-der-podcast-mit-checker-tobi/feed.xml")
anne_und_die_wilden_tiere = Podcast("https://feeds.br.de/anna-und-die-wilden-tiere/feed.xml")

tps = ToniePodcastSync("address-used-for-toniecloud@your-mailprovider.com", "toniecloud-password")

# uncomment the following lines if you want to print out
# a list of all your creative-tonies and their IDs
# and then exit this script:
#
# tps.print_tonies_overview()
# exit()

grauer_tonie = "A12345678901234Z"
piraten_tonie = "B12345678901234Z"

tps.sync_podcast_to_tonie(anne_und_die_wilden_tiere, grauer_tonie)
tps.sync_podcast_to_tonie(pumuckl, piraten_tonie)
