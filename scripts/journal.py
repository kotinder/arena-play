#!/usr/bin/env python3
"""The match journal — one JSONL file per match, plus a place for your notes.

This exists because of the single habit that separates an agent that improves
from one that just plays: after the match, read what happened and change
something. The journal is the raw material for that; the conclusions are
yours to write.

    ~/.arena-play/matches/ABCD2345.jsonl     every move, rejection and event
    ~/.arena-play/reviews/2026-08-02.md      what you concluded, in your words

Nothing here scores you or tells you what went wrong. A file that guessed at
that would be worse than an empty one: you would read the guess instead of
the game.
"""
from __future__ import annotations

import json
import time
from pathlib import Path


class Journal:
    def __init__(self, directory):
        self.dir = Path(directory)
        self.dir.mkdir(parents=True, exist_ok=True)

    def _write(self, code, record):
        record["at"] = time.time()
        path = self.dir / f"{code}.jsonl"
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def move(self, code, move, answer):
        self._write(code, {"kind": "move", "move": move,
                           "state": answer.get("state")})

    def rejected(self, code, move, reason):
        """Rejections are the most useful lines in the file: every one is a
        place where what you believed about the game was wrong."""
        self._write(code, {"kind": "rejected", "move": move, "reason": reason})

    def event(self, code, event):
        self._write(code, {"kind": "event", "event": event})

    def finish(self, code, view):
        self._write(code, {"kind": "finish", "result": view.get("result"),
                           "participants": view.get("participants")})

    # -- reading it back ------------------------------------------------------

    def read(self, code):
        path = self.dir / f"{code}.jsonl"
        if not path.exists():
            return []
        out = []
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                out.append(json.loads(line))
            except ValueError:
                continue
        return out

    def summary(self, code):
        """Enough to start a review: how it ended, and where you were wrong."""
        records = self.read(code)
        moves = [r for r in records if r["kind"] == "move"]
        rejected = [r for r in records if r["kind"] == "rejected"]
        finish = next((r for r in records if r["kind"] == "finish"), None)
        return {
            "code": code,
            "moves": len(moves),
            "rejected": len(rejected),
            "rejections": [r.get("reason") for r in rejected][:10],
            "result": (finish or {}).get("result"),
        }

    def matches(self):
        return sorted(p.stem for p in self.dir.glob("*.jsonl"))


if __name__ == "__main__":
    import argparse
    import os
    import sys

    home = Path(os.environ.get("ARENA_HOME", Path.home() / ".arena-play"))
    p = argparse.ArgumentParser(description="Read your match journal.")
    p.add_argument("code", nargs="?", help="match code; omit to list them all")
    args = p.parse_args()

    j = Journal(home / "matches")
    if not args.code:
        for code in j.matches():
            print(json.dumps(j.summary(code), ensure_ascii=False))
        sys.exit(0)
    print(json.dumps(j.summary(args.code), ensure_ascii=False, indent=2))
