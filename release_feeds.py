#!/usr/bin/env python3
"""Write one RSS feed per Pinterest board, holding only the pins whose release time has passed.

    python3 release_feeds.py

Runs daily in GitHub Actions (.github/workflows/pages.yml) and needs nothing but the standard
library. Pinterest reads each feed (feeds/<slug>.xml), creates a pin for every new item within a
day, and saves it to the board that feed was connected to. Items are listed newest first; an
item never changes once released, because Pinterest keys pins on the guid.
"""
import datetime as dt
import json
import os
from email.utils import format_datetime
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    with open(os.path.join(HERE, "pins", "schedule.json")) as f:
        pins = json.load(f)
    now = dt.datetime.now(dt.timezone.utc)
    os.makedirs(os.path.join(HERE, "feeds"), exist_ok=True)
    boards = {}
    for p in pins:
        boards.setdefault(p["slug"], {"board": p["board"], "link": p["link"], "items": []})
        if dt.datetime.fromisoformat(p["release"]) <= now:
            boards[p["slug"]]["items"].append(p)
    total = 0
    for slug, b in boards.items():
        items = sorted(b["items"], key=lambda p: p["release"], reverse=True)
        total += len(items)
        xml = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/">', "<channel>",
               f"<title>{escape(b['board'])} | Plainfield Press</title>",
               f"<link>{escape(b['link'])}</link>",
               f"<description>{escape(b['board'])}: free printables and pages from the Plainfield Press log books.</description>",
               "<language>en-us</language>"]
        for p in items:
            img = os.path.join(HERE, "pins", p["id"] + ".jpg")
            when = format_datetime(dt.datetime.fromisoformat(p["release"]))
            xml += ["<item>",
                    f"<title>{escape(p['title'])}</title>",
                    f"<link>{escape(p['link'])}</link>",
                    f"<description>{escape(p['description'])}</description>",
                    f'<guid isPermaLink="false">{escape(p["id"])}</guid>',
                    f"<pubDate>{when}</pubDate>",
                    f'<enclosure url="{escape(p["image"])}" length="{os.path.getsize(img)}" type="image/jpeg"/>',
                    f'<media:content url="{escape(p["image"])}" medium="image" type="image/jpeg" width="1000" height="1500"/>',
                    "</item>"]
        xml += ["</channel>", "</rss>"]
        with open(os.path.join(HERE, "feeds", f"{slug}.xml"), "w") as f:
            f.write("\n".join(xml) + "\n")
    print(f"{total} of {len(pins)} pins released across {len(boards)} feeds as of {now:%Y-%m-%d %H:%M} UTC")


if __name__ == "__main__":
    main()
