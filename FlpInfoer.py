"""FlpInfoer -- FL Studio .flp MIDI extraction tool
Python 3.10 + PyFlp 2.2.1 + mido
"""

import io
import os
import re
import sys
import time
import traceback
from collections import OrderedDict

from pyflp import parse
from pyflp.arrangement import PlaylistEvent

VERSION = "V0.3.1"


def _fix_stdout():
    """Ensure stdout uses utf-8 on Windows."""
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    else:
        try:
            sys.stdout = io.TextIOWrapper(
                sys.stdout.buffer, encoding="utf-8", errors="replace"
            )
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def calculate_fl_position(position, ppq):
    """Convert ticks to FL format bar:step:tick"""
    if not isinstance(position, (int, float)):
        try:
            position = int(position) if position else 0
        except Exception:
            position = 0
    tpb = ppq * 4
    bar = position // tpb + 1
    rem = position % tpb
    step = rem // 24
    tick = rem % 24
    return f"{bar}:{step:02d}:{tick:02d}"


def get_pitch_name(pitch_value):
    """MIDI note number -> note name"""
    if isinstance(pitch_value, int):
        notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        octave = (pitch_value // 12) - 1
        return f"{notes[pitch_value % 12]}{octave}"
    if isinstance(pitch_value, str):
        return pitch_value
    try:
        return str(pitch_value)
    except Exception:
        return "C5"


def _safe_int(value, default=0):
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return int(value)
    try:
        return int(value)
    except Exception:
        return default


# ---------------------------------------------------------------------------
# Parse
# ---------------------------------------------------------------------------

def create_channel_map(project):
    cmap = {}
    try:
        for i, ch in enumerate(project.channels):
            try:
                cid = getattr(ch, "id", i)
                cname = getattr(ch, "name", f"Track{i + 1}")
                cmap[cid] = cname
            except Exception:
                cmap[i] = f"Track{i + 1}"
    except Exception as e:
        print(f"Channel map failed: {e}")
    return cmap


def _consume_pattern_notes(project, channel_map):
    """Extract raw note data from all patterns.
    Returns: (tempo, ppq, {pname: [(pos,key,dur,ch_id,ch_name),...]}, total_count)
    """
    tempo = getattr(project, "tempo", 120.0)
    ppq = getattr(project, "ppq", 96)
    raw = OrderedDict()
    total = 0

    for i, pat in enumerate(project.patterns):
        name = getattr(pat, "name", f"Pattern_{i + 1}")
        notes_out = []
        raw_notes = list(getattr(pat, "notes", []))  # BUGFIX: generator -> list
        for note in raw_notes:
            try:
                pos = _safe_int(getattr(note, "position", 0))
                key = getattr(note, "key", 60)
                dur = _safe_int(
                    getattr(note, "duration", getattr(note, "length", 0)), 0
                )
                if dur <= 0:
                    dur = ppq // 4  # default 1/16
                ch = _safe_int(
                    getattr(note, "rack_channel", getattr(note, "channel", -1)), -1
                )
                ch_name = channel_map.get(ch, f"Track{ch + 1}")
                notes_out.append((pos, key, dur, ch, ch_name))
            except Exception as e:
                print(f"  Skip bad note: {e}")
        raw[name] = notes_out
        total += len(notes_out)

    return tempo, ppq, raw, total


def parse_playlist(project, pattern_index_by_name):
    """Parse playlist -> track sequences.
    Returns: {track_id: {"name": str, "events": [{pattern_name,start,length,end}]}}
    """
    track_seqs = OrderedDict()

    if not hasattr(project, "arrangements") or not project.arrangements:
        return track_seqs

    arr = project.arrangements[0]

    # Find PlaylistEvent in events
    ple = None
    for ev in getattr(arr, "events", []):
        if isinstance(ev, PlaylistEvent):
            ple = ev
            break
    if ple is None:
        ple = getattr(arr, "playlist", None)

    if ple is None or not hasattr(ple, "__len__"):
        return track_seqs

    items = list(ple)
    print(f"  Playlist items: {len(items)}")

    track_cursor = {}
    patterns_list = project.patterns  # for resolving FL ID -> name

    for item in items:
        raw_track = getattr(item, "track_index", None) or getattr(item, "track", None)
        rvidx = getattr(item, "track_rvidx", None)
        if raw_track is None and rvidx is not None and rvidx >= 0:
            raw_track = 500 - rvidx
        if raw_track is None:
            raw_track = 0

        length = _safe_int(getattr(item, "length", 384), 384)
        start = getattr(item, "start", None)
        if start is None:
            start = track_cursor.get(raw_track, 0)
        else:
            start = _safe_int(start)

        # Resolve pattern name
        pat_obj = getattr(item, "pattern", None)
        if pat_obj is not None:
            pname = getattr(pat_obj, "name", None)
        else:
            pname = None

        if pname is None:
            iidx = _safe_int(getattr(item, "item_index", 0), -1)
            pbase = _safe_int(getattr(item, "pattern_base", 0), 0)
            flpid = iidx - pbase - 1  # convert to 0-based pattern list index
            if 0 <= flpid < len(patterns_list):
                pname = getattr(patterns_list[flpid], "name", f"Pattern_{flpid + 1}")
            else:
                pname = f"Pattern_{iidx - pbase}"

        if raw_track not in track_seqs:
            track_seqs[raw_track] = {"name": f"Track{raw_track}", "events": []}

        track_seqs[raw_track]["events"].append({
            "pattern_name": pname,
            "start": start,
            "length": length,
            "end": start + length,
        })
        track_cursor[raw_track] = start + length

    return track_seqs


# ---------------------------------------------------------------------------
# Text export
# ---------------------------------------------------------------------------

def export_results(flp_path, raw_patterns, tempo, ppq):
    if not raw_patterns:
        print("No notes found, skip text export.")
        return

    base = os.path.splitext(os.path.basename(flp_path))[0]

    all_path = f"{base}_all_notes.txt"
    with open(all_path, "w", encoding="utf-8") as f:
        f.write(f"# FL Studio Note Extraction Tool {VERSION}\n")
        f.write(f"# File: {os.path.basename(flp_path)}\n")
        f.write(f"# Tempo: {tempo} BPM\n")
        f.write(f"# PPQ: {ppq}\n")
        f.write("# Format: [start-end,pitch,instrument] (duration=ticks)\n\n")

        for pname, notes in raw_patterns.items():
            f.write(f"\n{'=' * 80}\n# Pattern: {pname}\n{'=' * 80}\n\n")
            for pos, key, dur, ch, ch_name in notes:
                s = calculate_fl_position(pos, ppq)
                e = calculate_fl_position(pos + dur, ppq)
                pn = get_pitch_name(key)
                f.write(f"[{s}-{e},{pn},{ch_name}] dur={dur}ticks\n")

    print(f"[OK] All notes -> {all_path}")

    pdir = f"{base}_patterns"
    os.makedirs(pdir, exist_ok=True)
    for pname, notes in raw_patterns.items():
        safe = "".join(c if c.isalnum() or c in " -_" else "_" for c in pname)
        pp = os.path.join(pdir, f"{safe}.txt")
        with open(pp, "w", encoding="utf-8") as f:
            f.write(f"# Pattern: {pname}\n")
            for pos, key, dur, ch, ch_name in notes:
                s = calculate_fl_position(pos, ppq)
                e = calculate_fl_position(pos + dur, ppq)
                pn = get_pitch_name(key)
                f.write(f"[{s}-{e},{pn},{ch_name}] dur={dur}ticks\n")
        print(f"[OK] Pattern {pname} -> {pp}")


def export_track_sequences(flp_path, track_seqs, ppq):
    if not track_seqs:
        return
    base = os.path.splitext(os.path.basename(flp_path))[0]
    path = f"{base}_track_sequences.txt"
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# FL Studio Track Sequence Analysis {VERSION}\n")
        f.write(f"# File: {os.path.basename(flp_path)}\n")
        f.write(f"# Found {len(track_seqs)} track(s) with patterns\n\n")
        for tid, td in sorted(track_seqs.items(), key=lambda x: x[0]):
            f.write(f"### Track: {td['name']}\n")
            for ev in td["events"]:
                s = calculate_fl_position(ev["start"], ppq)
                e = calculate_fl_position(ev["end"], ppq)
                f.write(f"[{s}-{e}] {ev['pattern_name']} (dur={ev['length']}ticks)\n")
            f.write("\n")
    print(f"[OK] Track sequences -> {path}")


# ---------------------------------------------------------------------------
# MIDI export
# ---------------------------------------------------------------------------

_NOTE_MAP = {
    "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3,
    "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8,
    "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11,
}


def _midi_note_number(key):
    """Convert key (int or 'C5' string) to MIDI note number 0-127."""
    if isinstance(key, int):
        return max(0, min(127, key))
    key = str(key).strip()
    m = re.match(r"^([A-Ga-g]#?|[A-Ga-g]b)\s*(-?\d+)?$", key)
    if m:
        note = m.group(1).capitalize()
        octave = int(m.group(2)) if m.group(2) else 5
        base = _NOTE_MAP.get(note, 0)
        return max(0, min(127, (octave + 1) * 12 + base))
    # fallback: try int
    try:
        return max(0, min(127, int(key)))
    except Exception:
        return 60


def _write_midi_track(mid, ch_id, ch_name, notes, ppq, tempo, midi_channel):
    """Append a MIDI track to mid (MidiFile) with given notes.
    notes: [(tick, key, dur), ...]
    midi_channel: 0-15 MIDI channel number
    """
    from mido import Message, MetaMessage, MidiTrack

    track = MidiTrack()
    track.append(MetaMessage("track_name", name=ch_name, time=0))

    # Sort by time, then note-off before note-on at same position
    events = []
    for pos, key, dur in notes:
        nn = _midi_note_number(key)
        vel = 100
        events.append((pos, "note_on", nn, vel))
        events.append((pos + dur, "note_off", nn, 0))
    events.sort(key=lambda x: (x[0], 0 if x[1] == "note_off" else 1))

    last_tick = 0
    for tick, etype, nn, vel in events:
        delta = tick - last_tick
        if delta < 0:
            delta = 0
        if etype == "note_on":
            track.append(Message("note_on", channel=midi_channel, note=nn, velocity=vel, time=delta))
        else:
            track.append(Message("note_off", channel=midi_channel, note=nn, velocity=0, time=delta))
        last_tick = tick

    mid.tracks.append(track)


def export_pattern_midi(raw_patterns, tempo, ppq, flp_path):
    """One .mid per pattern."""
    from mido import MidiFile, MidiTrack, MetaMessage

    base = os.path.splitext(os.path.basename(flp_path))[0]
    mdir = f"{base}_midi_patterns"
    os.makedirs(mdir, exist_ok=True)

    for pname, notes in raw_patterns.items():
        if not notes:
            continue
        mid = MidiFile(ticks_per_beat=ppq)
        t0 = MidiTrack()
        mid.tracks.append(t0)
        t0.append(MetaMessage("set_tempo", tempo=int(60_000_000 / tempo), time=0))

        # Group by channel
        ch_groups = OrderedDict()
        for pos, key, dur, ch_id, ch_name in notes:
            if ch_id not in ch_groups:
                ch_groups[ch_id] = {"name": ch_name, "notes": []}
            ch_groups[ch_id]["notes"].append((pos, key, dur))

        for idx, (ch_id, ch_data) in enumerate(ch_groups.items()):
            _write_midi_track(mid, ch_id, ch_data["name"], ch_data["notes"], ppq, tempo, idx % 16)

        safe = "".join(c if c.isalnum() or c in " -_" else "_" for c in pname)
        mpath = os.path.join(mdir, f"{safe}.mid")
        mid.save(mpath)
        print(f"[OK] Pattern MIDI {pname} -> {mpath}")


def export_track_midi(raw_patterns, track_seqs, tempo, ppq, flp_path):
    """One .mid per track -- merge all patterns on that track by timeline."""
    if not track_seqs:
        return
    from mido import MidiFile, MidiTrack, MetaMessage

    base = os.path.splitext(os.path.basename(flp_path))[0]
    mdir = f"{base}_midi_tracks"
    os.makedirs(mdir, exist_ok=True)

    # name -> notes index
    pnotes = {}
    for pname, notes in raw_patterns.items():
        pnotes[pname] = notes

    for tid, td in sorted(track_seqs.items(), key=lambda x: x[0]):
        mid = MidiFile(ticks_per_beat=ppq)
        t0 = MidiTrack()
        mid.tracks.append(t0)
        t0.append(MetaMessage("set_tempo", tempo=int(60_000_000 / tempo), time=0))

        ch_all = OrderedDict()
        for ev in td["events"]:
            pn = ev["pattern_name"]
            offset = ev["start"]
            if pn in pnotes:
                for pos, key, dur, ch_id, ch_name in pnotes[pn]:
                    if ch_id not in ch_all:
                        ch_all[ch_id] = {"name": ch_name, "notes": []}
                    ch_all[ch_id]["notes"].append((pos + offset, key, dur))

        for idx, (ch_id, ch_data) in enumerate(ch_all.items()):
            _write_midi_track(
                mid, ch_id, ch_data["name"], ch_data["notes"], ppq, tempo, idx % 16
            )

        safe = "".join(c if c.isalnum() or c in " -_" else "_" for c in td["name"])
        mpath = os.path.join(mdir, f"{safe}.mid")
        mid.save(mpath)
        print(f"[OK] Track MIDI {td['name']} -> {mpath}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def extract_flp_notes(flp_path):
    print(f"\n{'=' * 50}")
    print(f"FlpInfoer {VERSION}")
    print(f"{'=' * 50}\n")
    print(f"Analyzing: {os.path.basename(flp_path)}")

    t0 = time.time()

    try:
        print("Loading...")
        project = parse(flp_path)
        ppq = getattr(project, "ppq", 96)
        tempo = getattr(project, "tempo", 120.0)
        print(f"Loaded  Tempo={tempo} BPM  PPQ={ppq}")

        channel_map = create_channel_map(project)

        print("\nParsing notes...")
        _, _, raw_patterns, total = _consume_pattern_notes(project, channel_map)
        print(f"Found {total} notes in {len(raw_patterns)} pattern(s)")

        ptn_names = list(raw_patterns.keys())
        pattern_index_by_name = {n: i for i, n in enumerate(ptn_names)}

        # Text export
        print("\n--- Text Export ---")
        export_results(flp_path, raw_patterns, tempo, ppq)

        # Playlist
        print("\n--- Playlist ---")
        track_seqs = parse_playlist(project, pattern_index_by_name)
        if track_seqs:
            export_track_sequences(flp_path, track_seqs, ppq)

        # MIDI export
        print("\n--- MIDI Export ---")
        print("Pattern MIDI...")
        export_pattern_midi(raw_patterns, tempo, ppq, flp_path)

        if track_seqs:
            print("Track MIDI...")
            export_track_midi(raw_patterns, track_seqs, tempo, ppq, flp_path)

        print(f"\n{'=' * 50}")
        print("All done!")

    except Exception as e:
        print(f"\nError: {e}")
        traceback.print_exc()

    print(f"Time: {time.time() - t0:.2f}s")


def main():
    _fix_stdout()
    print(f"FL Studio Note Extraction Tool {VERSION}")

    if len(sys.argv) < 2:
        print("\nDrag .flp file here or enter path: ", end="")
        flp_path = input().strip('"')
    else:
        flp_path = sys.argv[1]

    flp_path = flp_path.strip('"')

    if not os.path.isfile(flp_path):
        print(f"\nError: file not found: {flp_path}")
        print("\nPress Enter to exit...")
        input()
        return

    sys.setrecursionlimit(10000)

    if not flp_path.lower().endswith(".flp"):
        print(f"\nWarning: not a .flp file: {flp_path}")

    extract_flp_notes(flp_path)
    print("\nPress Enter to exit...")
    try:
        input()
    except (EOFError, OSError):
        pass


if __name__ == "__main__":
    main()
