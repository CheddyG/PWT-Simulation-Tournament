#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional, Tuple

# ---- dependency (install: pip install pokemon-showdown-replays) ----
try:
    from pokemon_showdown_replays import Download, Replay
except Exception as e:
    raise SystemExit(
        "Missing dependency: pokemon-showdown-replays\n"
        "Install it with:\n"
        "  pip install pokemon-showdown-replays\n"
        f"Original import error: {e}"
    )

START = "[[[[["
END = "]]]]]"


@dataclass
class BattleBlock:
    header: str
    protocol_lines: list[str]  # only lines starting with '|'


# ---------------- parsing battles from output1.txt ----------------
def iter_battles_marked(path: Path) -> Iterator[BattleBlock]:
    """Parse battles in [[[[[ ... ]]]]] blocks: first non-empty line is header, then protocol lines."""
    in_block = False
    waiting_for_header = False
    header: Optional[str] = None
    protocol_lines: list[str] = []

    with path.open("r", encoding="utf-8", errors="replace") as f:
        for raw in f:
            line = raw.rstrip("\n")

            if not in_block:
                if line.strip() == START:
                    in_block = True
                    waiting_for_header = True
                    header = None
                    protocol_lines = []
                continue

            # inside a block
            if line.strip() == END:
                yield BattleBlock(header or "UNKNOWN_MATCHUP", protocol_lines)
                in_block = False
                waiting_for_header = False
                header = None
                protocol_lines = []
                continue

            if waiting_for_header:
                if line.strip():
                    header = line.strip()
                    waiting_for_header = False
                continue

            if line.startswith("|"):
                protocol_lines.append(line)


def parse_single_battle_fallback(path: Path) -> BattleBlock:
    """
    If file isn't marker-wrapped, treat it as one battle:
    - header = first non-empty non-protocol line (or UNKNOWN_MATCHUP)
    - protocol = all lines starting with '|'
    """
    header = None
    protocol_lines: list[str] = []

    with path.open("r", encoding="utf-8", errors="replace") as f:
        for raw in f:
            line = raw.rstrip("\n")
            if not line.strip():
                continue
            if header is None and not line.startswith("|"):
                header = line.strip()
                continue
            if line.startswith("|"):
                protocol_lines.append(line)

    return BattleBlock(header or "UNKNOWN_MATCHUP", protocol_lines)


def iter_battles(path: Path) -> Iterator[BattleBlock]:
    # Peek once to decide if marker format exists
    text = path.read_text(encoding="utf-8", errors="replace")
    if START in text and END in text:
        # re-read streaming for memory safety
        yield from iter_battles_marked(path)
    else:
        yield parse_single_battle_fallback(path)


def get_battle_by_index(path: Path, index: int) -> BattleBlock:
    for i, block in enumerate(iter_battles(path)):
        if i == index:
            return block
    raise IndexError(f"Battle index {index} out of range.")


def get_battle_by_matchup(path: Path, matchup: str, occurrence: int = 0) -> BattleBlock:
    target = matchup.strip().lower()
    hits = 0
    for block in iter_battles(path):
        if block.header.strip().lower() == target:
            if hits == occurrence:
                return block
            hits += 1
    raise ValueError(f'No matchup "{matchup}" found at occurrence {occurrence}.')


def list_matchups(path: Path, top_n: int = 80) -> None:
    counts = Counter()
    total = 0
    for block in iter_battles(path):
        counts[block.header] += 1
        total += 1

    if total == 0:
        print("No battles found.")
        return

    print(f"Found {total} battle(s) across {len(counts)} unique matchup header(s):")
    for hdr, c in counts.most_common(top_n):
        print(f"{c:5d}  {hdr}")


# ---------------- overriding player names + avatars ----------------
def override_players(
    protocol_lines: list[str],
    p1_name: Optional[str] = None,
    p2_name: Optional[str] = None,
    p1_avatar: Optional[str] = None,
    p2_avatar: Optional[str] = None,
) -> list[str]:
    """
    Replace/insert |player| lines for p1/p2 so the replay shows chosen names + avatars.

    Showdown line format:
      |player|p1|Name|Avatar|
    """
    out = protocol_lines[:]

    def fix_player_line(line: str, name: Optional[str], avatar: Optional[str]) -> str:
        parts = line.split("|")  # ["", "player", "p1", "Name", "Avatar", ...]
        while len(parts) < 6:
            parts.append("")
        if name is not None:
            parts[3] = str(name)
        if avatar is not None:
            parts[4] = str(avatar)
        return "|".join(parts)

    found_p1 = False
    found_p2 = False

    for i, ln in enumerate(out):
        if ln.startswith("|player|p1|"):
            out[i] = fix_player_line(ln, p1_name, p1_avatar)
            found_p1 = True
        elif ln.startswith("|player|p2|"):
            out[i] = fix_player_line(ln, p2_name, p2_avatar)
            found_p2 = True

    # Insert near the top (before |start| if possible)
    insert_at = 0
    for i, ln in enumerate(out):
        if ln.startswith("|start|"):
            insert_at = i
            break

    if not found_p1 and (p1_name is not None or p1_avatar is not None):
        name = p1_name or "p1"
        avatar = p1_avatar or "1"
        out.insert(insert_at, f"|player|p1|{name}|{avatar}|")

    if not found_p2 and (p2_name is not None or p2_avatar is not None):
        name = p2_name or "p2"
        avatar = p2_avatar or "1"
        out.insert(insert_at, f"|player|p2|{name}|{avatar}|")

    return out


def sanitize_roomid(s: str, fallback: str = "sim") -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "", s)
    return (s or fallback)[:64]


# ---------------- building replay html ----------------
def build_replay_object(protocol_lines: list[str], roomid: str, show_full_damage: bool) -> dict:
    """
    Convert protocol lines to the replay JSON object expected by pokemon_showdown_replays.
    """
    p1 = "p1"
    p2 = "p2"
    fmt = "Custom Game"
    ts: Optional[str] = None

    for ln in protocol_lines:
        if ln.startswith("|player|p1|"):
            parts = ln.split("|")
            if len(parts) > 3 and parts[3]:
                p1 = parts[3]
        elif ln.startswith("|player|p2|"):
            parts = ln.split("|")
            if len(parts) > 3 and parts[3]:
                p2 = parts[3]
        elif ln.startswith("|tier|"):
            parts = ln.split("|")
            if len(parts) > 2 and parts[2]:
                fmt = parts[2]
        elif ts is None and ln.startswith("|t:|"):
            # Commonly unix seconds; best-effort conversion
            try:
                epoch = int(ln.split("|")[2])
                ts = datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%a %b %d %Y %H:%M:%S")
            except Exception:
                ts = None

    if ts is None:
        ts = datetime.now(timezone.utc).strftime("%a %b %d %Y %H:%M:%S")

    log_lines = protocol_lines[:] + [""]  # library expects last line empty

    log_dict = {
        "p1": p1,
        "p2": p2,
        "log": log_lines,
        "inputLog": "",
        "roomid": roomid,
        "format": fmt,
        "timestamp": ts,
    }

    return Replay.create_replay_object(log_dict, show_full_damage=show_full_damage)


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Convert TestOutput/output1.txt (many battles) into a Pokemon Showdown replay HTML."
    )

    # Paths (default matches your request)
    ap.add_argument("--folder", type=Path, default=Path("TestOutput"))
    ap.add_argument("--input", type=str, default="output1.txt")
    ap.add_argument("--output", type=str, default="replay.html")

    # Choosing which battle
    ap.add_argument("--battle-index", type=int, default=None, help="Pick battle by index (0-based). Default 0.")
    ap.add_argument("--matchup", type=str, default=None, help='Pick by header, exact match e.g. "Alder vs Alder"')
    ap.add_argument("--occurrence", type=int, default=0, help="If multiple matchups match, pick Nth occurrence.")
    ap.add_argument("--list-matchups", action="store_true", help="Print matchup headers + counts and exit.")

    # Override names/avatars (official Showdown avatar IDs)
    ap.add_argument("--p1-name", type=str, default=None)
    ap.add_argument("--p2-name", type=str, default=None)
    ap.add_argument("--p1-avatar", type=str, default=None, help="Official Showdown avatar id (number as string)")
    ap.add_argument("--p2-avatar", type=str, default=None, help="Official Showdown avatar id (number as string)")
    ap.add_argument("--both-name", type=str, default=None, help="Set both p1 and p2 names")
    ap.add_argument("--both-avatar", type=str, default=None, help="Set both p1 and p2 avatars")

    # Replay settings
    ap.add_argument("--show-full-damage", action="store_true")
    ap.add_argument("--embed-base", default="https://play.pokemonshowdown.com")  # official showdown

    args = ap.parse_args()

    input_path = args.folder / args.input
    output_path = args.folder / args.output

    if not input_path.exists():
        raise SystemExit(f"Input not found: {input_path}")

    if args.list_matchups:
        list_matchups(input_path)
        return

    # Select battle
    if args.matchup is not None:
        block = get_battle_by_matchup(input_path, args.matchup, args.occurrence)
        roomid = sanitize_roomid(f"{args.matchup}-{args.occurrence}", fallback="sim")
    else:
        idx = 0 if args.battle_index is None else args.battle_index
        block = get_battle_by_index(input_path, idx)
        roomid = sanitize_roomid(f"sim-battle-{idx}", fallback="sim")

    # Apply overrides
    p1_name = args.p1_name or args.both_name
    p2_name = args.p2_name or args.both_name
    p1_avatar = args.p1_avatar or args.both_avatar
    p2_avatar = args.p2_avatar or args.both_avatar

    protocol = override_players(
        block.protocol_lines,
        p1_name=p1_name,
        p2_name=p2_name,
        p1_avatar=p1_avatar,
        p2_avatar=p2_avatar,
    )

    replay_obj = build_replay_object(protocol, roomid=roomid, show_full_damage=args.show_full_damage)

    html = Download.create_replay(
        replay_obj,
        replay_embed_location=f"{args.embed_base.rstrip('/')}/js/replay-embed.js",
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")

    print(f"Wrote: {output_path}")
    print(f"Selected battle header: {block.header}")
    if p1_name or p2_name or p1_avatar or p2_avatar:
        print(f"Overrides -> p1: name={p1_name} avatar={p1_avatar} | p2: name={p2_name} avatar={p2_avatar}")
    print("If it doesn't play from file://, do:")
    print(f"  cd {args.folder}")
    print("  python -m http.server 8001")
    print(f"Then open: http://localhost:8001/{output_path.name}")


if __name__ == "__main__":
    main()
