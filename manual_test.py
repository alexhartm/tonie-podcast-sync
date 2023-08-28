from toniepodcastsync import ToniePodcastSync
from podcast import Podcast


def main():
    tps = ToniePodcastSync("meierhofwilli@gmail.com", "U6ECoZ3jKo3HnB!jt3NX3")
    tps.print_tonies_overview()
    podcast = Podcast("https://feeds.br.de/lachlabor/feed.xml")
    tps.sync_podcast_to_tonie(podcast, "C295B412500304E0")
    tps.sync_podcast_to_tonie(Podcast("https://www.kakadu.de/kakadu-104.xml"), "8561BE13500304E0")


if __name__ == "__main__":
    main()
