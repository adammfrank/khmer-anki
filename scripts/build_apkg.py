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
# creating duplicates in Anki. Keep MODEL_ID stable across field/template
# changes -- Anki matches notetypes by this ID and updates it in place, and
# matches notes by guid_for(id) below, which lets re-imports update existing
# cards' content without resetting their review scheduling.
MODEL_ID = 1607392319
DECK_ID = 2059412232

# Khmer stacks vowel/diacritic marks above and below the consonant line, so it
# needs a generous line-height and a Khmer-capable font or glyphs clip. The
# font stack covers macOS, Windows, Android and the Anki desktop default.
CSS = """
.card {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  font-size: 20px;
  text-align: center;
  color: #22303c;
  background-color: #fbfbfd;
  padding: 28px 18px;
}
.card.nightMode, .nightMode .card {
  color: #e6e8ea;
  background-color: #2c2c2e;
}

.english {
  font-size: 30px;
  font-weight: 500;
  line-height: 1.4;
}

.khmer {
  font-family: "Noto Sans Khmer", "Khmer OS", "Khmer Sangam MN",
               "Leelawadee UI", "Nirmala UI", sans-serif;
  font-size: 46px;
  line-height: 1.9;
  padding: 4px 0;
}

.roman {
  font-size: 17px;
  font-style: italic;
  letter-spacing: 0.4px;
  color: #7c8894;
  margin-top: 2px;
}
.card.nightMode .roman, .nightMode .card .roman { color: #9aa4ae; }

.audio { margin-top: 14px; }

hr#answer {
  border: none;
  border-top: 1px solid #dfe3e8;
  width: 55%;
  margin: 22px auto;
}
.card.nightMode hr#answer, .nightMode .card hr#answer { border-top-color: #45464a; }
"""

MODEL = genanki.Model(
    MODEL_ID,
    "Khmer Basic",
    fields=[{"name": "English"}, {"name": "Khmer"}, {"name": "Romanization"}, {"name": "Audio"}],
    css=CSS,
    templates=[
        {
            "name": "English -> Khmer",
            "qfmt": '<div class="english">{{English}}</div>',
            "afmt": '{{FrontSide}}<hr id="answer">'
                    '<div class="khmer">{{Khmer}}</div>'
                    '<div class="roman">{{Romanization}}</div>'
                    '<div class="audio">{{Audio}}</div>',
        },
        {
            "name": "Khmer -> English",
            "qfmt": '<div class="khmer">{{Khmer}}</div>'
                    '<div class="roman">{{Romanization}}</div>'
                    '<div class="audio">{{Audio}}</div>',
            "afmt": '{{FrontSide}}<hr id="answer">'
                    '<div class="english">{{English}}</div>',
        },
    ],
)


def main():
    with open(CSV_PATH, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    deck = genanki.Deck(DECK_ID, "Khmer - Top 100 Beginner Words")
    media_files = []
    missing = []

    for position, row in enumerate(rows, start=1):
        mp3_name = f"{row['id']}.mp3"
        mp3_path = os.path.join(MEDIA_DIR, mp3_name)
        if not os.path.exists(mp3_path):
            missing.append(mp3_name)
            audio_field = ""
        else:
            media_files.append(mp3_path)
            audio_field = f"[sound:{mp3_name}]"

        # genanki defaults every card to new-queue position 0, which makes
        # Anki's default "Card type, then order gathered" ordering introduce
        # all 100 English->Khmer cards before any Khmer->English one. Real Anki
        # gives each note a sequential position that both of its cards share,
        # so a day's new cards gather both directions of the same word together.
        note = genanki.Note(
            model=MODEL,
            fields=[row["english"], row["khmer"], row["romanization"], audio_field],
            guid=genanki.guid_for(row["id"]),
            due=position,
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
