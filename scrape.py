import argparse
import os
from pathlib import Path

import bs4
import httpx
from bs4 import Tag
from httpx import URL
from pydantic import TypeAdapter

from models import BookInfo, Chapter

# All of these have been manually fixed with my local HTML files:
#
# could not find Summary tag for hout/03/C29.html -          https://library.tarvalon.net/index.php?title=The_Dragon_Reborn:_Chapter_29
# could not find Summary tag for hout/06/C40.html -          https://library.tarvalon.net/index.php?title=Lord_of_Chaos:_Chapter_40
# could not find parent H2 of Summary for hout/07/C01.html - https://library.tarvalon.net/index.php?title=A_Crown_of_Swords:_Chapter_1
# could not find Summary tag for hout/07/C32.html -          https://library.tarvalon.net/index.php?title=A_Crown_of_Swords:_Chapter_32
#
# Problem: I think Summary and Outline are swapped
# https://library.tarvalon.net/index.php?title=A_Crown_of_Swords:_Chapter_33
# https://library.tarvalon.net/index.php?title=The_Eye_of_the_World:_Chapter_27
#
# Repeated Summary or malformed pages:
# https://library.tarvalon.net/index.php?title=The_Fires_of_Heaven:_Chapter_10


# Root URL
root = "https://library.tarvalon.net"
hout = "hout"
data = "data"

parser = argparse.ArgumentParser()
parser.add_argument(
    "-f", "--fetch", action="store_true", help="Fetch HTML for all pages"
)
args = parser.parse_args()


def get_main_pages() -> list[BookInfo]:
    """
    Fetch all chapter summary pages and the listings within them
    """

    result = []

    # Taken from https://library.tarvalon.net/index.php?title=Chapter_Summaries
    # fmt: off
    paths = [
        ("New Spring", "/index.php?title=New_Spring:_Chapter_Summaries"),
        ("The Eye of the World", "/index.php?title=The_Eye_of_the_World:_Chapter_Summaries"),
        ("The Great Hunt", "/index.php?title=The_Great_Hunt:_Chapter_Summaries"),
        ("The Dragon Reborn", "/index.php?title=The_Dragon_Reborn:_Chapter_Summaries"),
        ("The Shadow Rising", "/index.php?title=The_Shadow_Rising:_Chapter_Summaries"),
        ("The Fires of Heaven", "/index.php?title=The_Fires_of_Heaven:_Chapter_Summaries"),
        ("Lord of Chaos", "/index.php?title=Lord_of_Chaos:_Chapter_Summaries"),
        ("A Crown of Swords", "/index.php?title=A_Crown_of_Swords:_Chapter_Summaries"),
        ("The Path of Daggers", "/index.php?title=The_Path_of_Daggers:_Chapter_Summaries"),
        ("Winter's Heart", "/index.php?title=Winter%27s_Heart:_Chapter_Summaries"),
        ("Crossroads of Twilight", "/index.php?title=Crossroads_of_Twilight:_Chapter_Summaries"),
        ("Knife of Dreams", "/index.php?title=Knife_of_Dreams:_Chapter_Summaries"),
        ("The Gathering Storm", "/index.php?title=The_Gathering_Storm:_Chapter_Summaries"),
        ("Towers of Midnight", "/index.php?title=Towers_of_Midnight:_Chapter_Summaries"),
        ("A Memory of Light", "/index.php?title=A_Memory_of_Light:_Chapter_Summaries"),
    ]
    # fmt: on

    for i, (name, path) in enumerate(paths):
        url = URL(f"{root}{path}")
        out_path = Path(f"{hout}/book_index_{i}.html")

        result.append(
            BookInfo(
                idx=f"{i:02}",
                source=str(url),
                book_name=name,
                path=str(out_path),
                chapters=[],
            )
        )

        if args.fetch:
            os.makedirs(hout, exist_ok=True)

            print(f"GET {url}")
            response = httpx.get(url, timeout=None)

            assert response.status_code == 200, (
                f"Failed to fetch {url}, got {response.status_code}"
            )

            print(f"Writing to {out_path}")
            with open(out_path, "w") as file:
                file.write(response.text)
        else:
            print(f"Skipping index generation {name}")

    return result


def get_chapter_links(infos: list[BookInfo]) -> list[BookInfo]:
    """
    Gets all chapter links and titles from the Chapter Summaries page
    """

    for info in infos:
        with Path(info.path).open() as file:
            content = file.read()
            html = bs4.BeautifulSoup(content, "html.parser")

            div_tag = html.select_one("#mw-content-text")

            if div_tag is None:
                print(f"could not find div tag for {info.book_name}")
                continue

            chapters = []

            for idx, anchor in enumerate(div_tag.select("ul li a")):
                href = anchor.get("href")
                text = anchor.text

                if href is None or text is None:
                    print(
                        f"could not get a chapter link or text for {info.book_name}. Got: {href}, {text}"
                    )
                    continue

                chapters.append(
                    Chapter(
                        idx=idx,
                        name=text,
                        link=str(href),
                        path="",
                        paragraphs=[],
                        title="",
                    )
                )

            info.chapters = chapters

    return infos


def get_chapter_pages(infos: list[BookInfo]) -> list[BookInfo]:
    """
    Fetches each chapter page for all books
    """

    if not args.fetch:
        print("Skipping fetching chapter pages")

    for info in infos:
        path_prefix = Path(f"{hout}/{info.idx}")

        os.makedirs(path_prefix, exist_ok=True)

        for i, chapter in enumerate(info.chapters):
            link = chapter.link
            chapter.path = f"{path_prefix}/C{i:02}.html"

            if args.fetch:
                url = URL(f"{root}{link}")

                print(f"GET {url}")
                response = httpx.get(url, timeout=None)

                assert response.status_code == 200, (
                    f"Failed to fetch {url}, got {response.status_code}"
                )

                print(f"Writting to {chapter.path}")
                with open(chapter.path, "w") as file:
                    file.write(response.text)

    return infos


skips = [
    "<<",
    "Setting:",
    "Characters:",
    "Chapter Icon:",
    "Points of view:",
    "Author:",
    "Location:",
]


def get_chapter_title(in_path: Path, soup: bs4.BeautifulSoup) -> str:
    # Assumption:
    # All titles are in this order of tags
    title = soup.select_one("#mw-content-text b center font")

    if title is None:
        print(f"could not find chapter title for {in_path}")
        return ""

    return str.strip(title.text)


def get_start_summary(in_path: Path, soup: bs4.BeautifulSoup) -> Tag | None:
    # Assumption:
    # the Summary is always an H2 -> Span -> Summary (text)
    # where the span has id="Summary"
    summary_span = soup.select_one("#Summary")

    if summary_span is None:
        print(f"could not find Summary tag for {in_path}")
        return None

    h2_summary = summary_span.parent

    if not h2_summary or h2_summary.name != "h2":
        print(f"could not find parent H2 of Summary for {in_path}")

    return h2_summary


def prepare_data(infos: list[BookInfo]) -> list[BookInfo]:
    for info in infos:
        in_dir = info.path

        for chapter in info.chapters:
            in_path = Path(chapter.path)

            content = in_path.read_text()
            soup = bs4.BeautifulSoup(content, "html.parser")

            chapter.title = get_chapter_title(in_path, soup)

            summary = get_start_summary(in_path, soup)

            if not summary:
                continue

            paragraphs = []
            chapter.paragraphs = paragraphs

            for maybe_p in summary.find_next_siblings():
                if maybe_p.name == "h2" or maybe_p.name == "h3":
                    break
                if maybe_p.name == "p":
                    # add a separator between tags, otherwise inline anchors' texts are concatenated to the previous word
                    # it's fine to have extra spaces within the text, I guess the TTS AI won't care
                    text = maybe_p.get_text(separator=" ", strip=True)

                    if len(text) > 0 and not (
                        sum([1 if text.startswith(pref) else 0 for pref in skips]) > 0
                    ):
                        paragraphs.append(text)

    return infos


def save_final_data(infos: list[BookInfo]):
    os.makedirs(data, exist_ok=True)

    with open(Path(f"{data}/output.json"), "wb") as file:
        adapter = TypeAdapter(list[BookInfo])

        file.write(adapter.dump_json(infos))


if __name__ == "__main__":
    infos = get_main_pages()
    infos = get_chapter_links(infos)
    infos = get_chapter_pages(infos)
    infos = prepare_data(infos)

    save_final_data(infos)

    print("Total page links", sum([len(link.chapters) for link in infos]))

    for info in infos:
        for chapter in info.chapters:
            if len(str(chapter.paragraphs)) < 500:
                print(f"Small chapter: {info.book_name}: {chapter.path}")
