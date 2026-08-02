#!/usr/bin/env python3
"""Generate Khmer TTS audio for data/khmer_100.csv using the Azure Speech REST API.

Requires AZURE_SPEECH_KEY and AZURE_SPEECH_REGION, either as environment
variables or in a .env file in the project root (loaded automatically).

Usage:
  python3 scripts/generate_audio.py --test          # first 5 rows only, into media/test/
  python3 scripts/generate_audio.py                 # all 100 rows, into media/
  python3 scripts/generate_audio.py --voice km-KH-PisethNeural
"""
import argparse
import csv
import os
import sys
import time
import xml.sax.saxutils as saxutils

import requests

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "khmer_100.csv")
ENV_PATH = os.path.join(os.path.dirname(__file__), "..", ".env")
DEFAULT_VOICE = "km-KH-SreymomNeural"
TOKEN_URL_FMT = "https://{region}.api.cognitive.microsoft.com/sts/v1.0/issueToken"
TTS_URL_FMT = "https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"


def load_dotenv(path: str) -> None:
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


def get_access_token(key: str, region: str) -> str:
    resp = requests.post(
        TOKEN_URL_FMT.format(region=region),
        headers={"Ocp-Apim-Subscription-Key": key},
    )
    if resp.status_code != 200:
        sys.exit(
            f"Failed to get Azure access token ({resp.status_code}): {resp.text}\n"
            "Check AZURE_SPEECH_KEY / AZURE_SPEECH_REGION."
        )
    return resp.text


def synthesize(token: str, region: str, khmer_text: str, voice: str) -> bytes:
    ssml = (
        '<speak version="1.0" xml:lang="km-KH">'
        f'<voice name="{voice}">{saxutils.escape(khmer_text)}</voice>'
        "</speak>"
    )
    resp = requests.post(
        TTS_URL_FMT.format(region=region),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "audio-24khz-48kbitrate-mono-mp3",
            "User-Agent": "khmer-anki-deck",
        },
        data=ssml.encode("utf-8"),
    )
    if resp.status_code != 200:
        raise RuntimeError(f"TTS request failed ({resp.status_code}): {resp.text}")
    return resp.content


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="Only generate the first 5 entries, into media/test/")
    parser.add_argument("--voice", default=DEFAULT_VOICE, help="Azure neural voice name")
    args = parser.parse_args()

    load_dotenv(ENV_PATH)
    key = os.environ.get("AZURE_SPEECH_KEY")
    region = os.environ.get("AZURE_SPEECH_REGION")
    if not key or not region:
        sys.exit("Set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION, either as env vars or in .env.")

    with open(CSV_PATH, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    if args.test:
        rows = rows[:5]
        out_dir = os.path.join(os.path.dirname(__file__), "..", "media", "test")
    else:
        out_dir = os.path.join(os.path.dirname(__file__), "..", "media")
    os.makedirs(out_dir, exist_ok=True)

    token = get_access_token(key, region)
    token_time = time.time()

    for i, row in enumerate(rows):
        # Azure access tokens expire after 10 minutes; refresh proactively.
        if time.time() - token_time > 540:
            token = get_access_token(key, region)
            token_time = time.time()

        out_path = os.path.join(out_dir, f"{row['id']}.mp3")
        print(f"[{i+1}/{len(rows)}] {row['english']} -> {row['khmer']} ({out_path})")
        audio = synthesize(token, region, row["khmer"], args.voice)
        with open(out_path, "wb") as f:
            f.write(audio)
        time.sleep(0.2)  # be polite to the API

    print(f"\nDone. Wrote {len(rows)} mp3 files to {out_dir}")


if __name__ == "__main__":
    main()
