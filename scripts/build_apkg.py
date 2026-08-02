#!/usr/bin/env python3
"""Build khmer_beginner_100.apkg from data/khmer_100.csv + media/*.mp3."""
import csv
import os
import sys

import genanki

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
CSV_PATH = os.path.join(BASE_DIR, "data", "khmer_100.csv")
MEDIA_DIR = os.path.join(BASE_DIR, "media")
OUT_PATH = os.path.join(BASE_DIR, "khmer_beginner_100.apkg")

# Fixed IDs so re-running this script updates the same deck/model instead of
# creating duplicates in Anki.
MODEL_ID = 1607392319
DECK_ID = 2059412232

MODEL = genanki.Model(
    MODEL_ID,
    "Khmer Basic",
    fields=[{"name": "English"}, {"name": "Khmer"}, {"name": "Audio"}],
    templates=[
        {
            "name": "English -> Khmer",
            "qfmt": '<div style="font-size:28px">{{English}}</div>',
            "afmt": '{{FrontSide}}<hr id="answer">'
                    '<div style="font-size:36px">{{Khmer}}</div>'
                    "{{Audio}}",
        },
        {
            "name": "Khmer -> English",
            "qfmt": '<div style="font-size:36px">{{Khmer}}</div>{{Audio}}',
            "afmt": '{{FrontSide}}<hr id="answer">'
                    '<div style="font-size:28px">{{English}}</div>',
        },
    ],
)


def main():
    with open(CSV_PATH, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    deck = genanki.Deck(DECK_ID, "Khmer - Top 100 Beginner Words")
    media_files = []
    missing = []

    for row in rows:
        mp3_name = f"{row['id']}.mp3"
        mp3_path = os.path.join(MEDIA_DIR, mp3_name)
        if not os.path.exists(mp3_path):
            missing.append(mp3_name)
            audio_field = ""
        else:
            media_files.append(mp3_path)
            audio_field = f"[sound:{mp3_name}]"

        note = genanki.Note(
            model=MODEL,
            fields=[row["english"], row["khmer"], audio_field],
            guid=genanki.guid_for(row["id"]),
        )
        deck.add_note(note)

    if missing:
        print(f"WARNING: {len(missing)} audio files missing (cards will have no sound): {missing[:5]}{'...' if len(missing) > 5 else ''}")

    package = genanki.Package(deck)
    package.media_files = media_files
    package.write_to_file(OUT_PATH)
    print(f"Wrote {OUT_PATH} with {len(rows)} notes ({len(rows)*2} cards) and {len(media_files)} audio files.")


if __name__ == "__main__":
    main()
