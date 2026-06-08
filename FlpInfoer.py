"""FlpInfoer -- FL Studio .flp MIDI extraction tool
Python 3.10 + PyFlp 2.2.1 + mido
"""

import io
import math
import os
import re
import shutil
import sys
import time
import traceback
from collections import OrderedDict

VERSION = "V0.5.0"
REQUIRED_PYTHON = (3, 10)


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

def _check_python_version():
    """PyFLP 2.2.1 is known to work with Python 3.10 in this project."""
    if sys.version_info[:2] == REQUIRED_PYTHON:
        return True

    current = f"{sys.version_info.major}.{sys.version_info.minor}"
    required = f"{REQUIRED_PYTHON[0]}.{REQUIRED_PYTHON[1]}"
    print(
        f"\nError: FlpInfoer {VERSION} requires Python {required}. "
        f"Current Python is {current}."
    )
    print("PyFLP 2.2.1 may fail before parsing .flp files on other Python versions.")
    return False


def calculate_fl_position(position, ppq):
    """Convert ticks to FL-style bar:step:tick notation."""
    if not isinstance(position, (int, float)):
        try:
            position = int(position) if position else 0
        except Exception:
            position = 0
    ticks_per_bar = ppq * 4
    ticks_per_step = max(1, ppq // 4)
    bar = position // ticks_per_bar + 1
    rem = position % ticks_per_bar
    step = rem // ticks_per_step
    tick = rem % ticks_per_step
    return f"{bar}:{step:02d}:{tick:02d}"


def get_pitch_name(pitch_value):
    """Return an FL/PyFLP-style note name for text output."""
    if isinstance(pitch_value, int):
        notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        octave = pitch_value // 12
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
        try:
            if isinstance(value, float) and not math.isfinite(value):
                return default
            return int(value)
        except Exception:
            return default
    try:
        return int(value)
    except Exception:
        return default


def _safe_getattr(obj, attr, default=None):
    """Read PyFLP properties that may raise when the backing event is absent."""
    try:
        value = getattr(obj, attr)
    except Exception:
        return default
    return default if value is None else value


def _safe_bool(value, default=False):
    if value is None:
        return default
    try:
        return bool(value)
    except Exception:
        return default


def _clamp(value, low, high):
    return max(low, min(high, value))


def _display_name(value, fallback):
    if value is None:
        return fallback
    value = str(value).strip()
    return value if value else fallback


def _safe_filename(name, fallback="untitled"):
    """Make a Windows-safe filename stem while keeping readable names."""
    name = _display_name(name, fallback)
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    name = re.sub(r"\s+", " ", name).strip(" .")
    if not name:
        name = fallback
    return name[:120]


def _indexed_stem(index, name, fallback):
    return f"{index:03d} - {_safe_filename(name, fallback)}"


def _unique_stem(name, used, fallback="untitled"):
    stem = _safe_filename(name, fallback)
    candidate = stem
    index = 2
    while candidate.lower() in used:
        candidate = f"{stem}_{index}"
        index += 1
    used.add(candidate.lower())
    return candidate


def _program_dir():
    """Directory where the script or bundled executable lives."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def _prepare_output_dir(flp_path):
    base = os.path.splitext(os.path.basename(flp_path))[0]
    out_name = _safe_filename(base, "FLP_Project")
    program_dir = os.path.abspath(_program_dir())
    output_dir = os.path.abspath(os.path.join(program_dir, out_name))

    if os.path.commonpath([program_dir, output_dir]) != program_dir:
        raise RuntimeError(f"Unsafe output directory: {output_dir}")
    if output_dir == program_dir:
        raise RuntimeError("Output directory cannot be the program directory.")

    if os.path.isdir(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def _channel_fallback(channel_id, index=None):
    if index is not None:
        number = index + 1
    elif isinstance(channel_id, int) and channel_id >= 0:
        number = channel_id + 1
    else:
        number = 0
    return f"NONAME_Channel{number:03d}"


def _channel_name(channel, fallback):
    for attr in ("display_name", "name", "internal_name"):
        value = _safe_getattr(channel, attr, None)
        if value:
            return _display_name(value, fallback)
    return fallback


def _pattern_label(pattern, index, used):
    iid = _safe_getattr(pattern, "iid", index + 1)
    name = _display_name(
        _safe_getattr(pattern, "name", None),
        f"NONAME{index + 1:03d}",
    )
    label = name
    suffix = 2
    while label.lower() in used:
        label = f"{name}_{suffix}"
        suffix += 1
    used.add(label.lower())
    return label


# ---------------------------------------------------------------------------
# Parse
# ---------------------------------------------------------------------------

def create_channel_info(project):
    info = OrderedDict()
    try:
        for i, ch in enumerate(project.channels):
            try:
                cid = _safe_getattr(ch, "iid", _safe_getattr(ch, "id", i))
                cid = _safe_int(cid, i)
                cname = _channel_name(ch, _channel_fallback(cid, i))
                enabled = _safe_bool(_safe_getattr(ch, "enabled", True), True)
                info[cid] = {"name": cname, "enabled": enabled}
            except Exception:
                info[i] = {"name": _channel_fallback(i, i), "enabled": True}
    except Exception as e:
        print(f"Channel info failed: {e}")
    return info


def create_channel_map(project):
    return {cid: data["name"] for cid, data in create_channel_info(project).items()}


def _consume_pattern_notes(project, channel_info):
    """Extract raw note data from all patterns.
    Returns:
        tempo, ppq, raw_patterns, total_count, pattern_labels_by_iid, note_stats
    """
    tempo = _safe_getattr(project, "tempo", 120.0)
    ppq = _safe_getattr(project, "ppq", 96)
    raw = OrderedDict()
    pattern_labels_by_iid = {}
    used_pattern_labels = set()
    total = 0
    note_stats = {
        "skipped_disabled_notes": 0,
        "disabled_channels": OrderedDict(),
    }

    for i, pat in enumerate(project.patterns):
        name = _pattern_label(pat, i, used_pattern_labels)
        iid = _safe_getattr(pat, "iid", i + 1)
        pattern_labels_by_iid[iid] = name
        notes_out = []
        raw_notes = list(_safe_getattr(pat, "notes", []))
        for note in raw_notes:
            try:
                pos = _safe_int(_safe_getattr(note, "position", 0))
                key = _safe_getattr(note, "key", 60)
                dur = _safe_int(
                    _safe_getattr(note, "duration", _safe_getattr(note, "length", 0)),
                    0,
                )
                if dur <= 0:
                    dur = ppq // 4  # default 1/16
                ch = _safe_int(
                    _safe_getattr(note, "rack_channel", _safe_getattr(note, "channel", -1)),
                    -1,
                )
                velocity = _safe_int(_safe_getattr(note, "velocity", 100), 100)
                ch_data = channel_info.get(
                    ch,
                    {"name": _channel_fallback(ch), "enabled": True},
                )
                ch_name = ch_data["name"]
                if not ch_data.get("enabled", True):
                    note_stats["skipped_disabled_notes"] += 1
                    note_stats["disabled_channels"][ch] = ch_name
                    continue
                notes_out.append((pos, key, dur, velocity, ch, ch_name))
            except Exception as e:
                print(f"  Skip bad note: {e}")
        raw[name] = notes_out
        total += len(notes_out)

    return tempo, ppq, raw, total, pattern_labels_by_iid, note_stats


def _item_offsets(item):
    offsets = _safe_getattr(item, "offsets", (0, 0))
    if not isinstance(offsets, (tuple, list)) or len(offsets) < 2:
        offsets = (0, 0)
    return _safe_int(offsets[0], 0), _safe_int(offsets[1], 0)


def parse_playlist(project, pattern_labels_by_iid):
    """Parse playlist -> track sequences.
    Returns:
        track_seqs,
        playlist_stats
    """
    track_seqs = OrderedDict()
    playlist_stats = {
        "skipped_disabled_tracks": [],
        "skipped_muted_items": [],
        "unsupported_items": [],
        "offset_items": [],
        "total_pattern_items": 0,
    }

    arrangements = list(_safe_getattr(project, "arrangements", []) or [])
    if not arrangements:
        return track_seqs, playlist_stats

    item_count = 0
    arr = arrangements[0]
    for track_index, track in enumerate(arr.tracks, start=1):
        track_id = _safe_int(_safe_getattr(track, "iid", track_index), track_index)
        track_name = _display_name(_safe_getattr(track, "name", None), f"Track{track_id}")
        track_enabled = _safe_bool(_safe_getattr(track, "enabled", True), True)
        events = []

        if not track_enabled:
            playlist_stats["skipped_disabled_tracks"].append(track_name)
            continue

        for item_index, item in enumerate(track, start=1):
            if _safe_bool(_safe_getattr(item, "muted", False), False):
                playlist_stats["skipped_muted_items"].append(
                    f"{track_name} item {item_index}"
                )
                continue

            pat_obj = _safe_getattr(item, "pattern", None)
            if pat_obj is None:
                playlist_stats["unsupported_items"].append(
                    f"{track_name} item {item_index}: {type(item).__name__}"
                )
                continue

            pattern_iid = _safe_getattr(pat_obj, "iid", None)
            pname = pattern_labels_by_iid.get(
                pattern_iid,
                _display_name(
                    _safe_getattr(pat_obj, "name", None),
                    f"Pattern_{pattern_iid}",
                ),
            )
            start = _safe_int(_safe_getattr(item, "position", _safe_getattr(item, "start", 0)), 0)
            length = _safe_int(_safe_getattr(item, "length", 0), 0)
            if length <= 0:
                length = _safe_int(_safe_getattr(pat_obj, "length", 0), 0)
            offset_start, offset_end = _item_offsets(item)
            if offset_start or offset_end:
                playlist_stats["offset_items"].append(
                    f"{track_name} / {pname}: start={offset_start}, end={offset_end}"
                )

            events.append({
                "pattern_name": pname,
                "start": start,
                "length": length,
                "end": start + length,
                "offset_start": offset_start,
                "offset_end": offset_end,
            })
            item_count += 1

        if events:
            track_seqs[track_id] = {"name": track_name, "events": events}

    print(f"  Playlist pattern items: {item_count}")
    playlist_stats["total_pattern_items"] = item_count

    return track_seqs, playlist_stats


# ---------------------------------------------------------------------------
# Text export
# ---------------------------------------------------------------------------

def export_results(output_dir, flp_path, raw_patterns, tempo, ppq):
    if not raw_patterns:
        print("No notes found, skip text export.")
        return 0

    all_path = os.path.join(output_dir, "all_notes.txt")
    with open(all_path, "w", encoding="utf-8") as f:
        f.write(f"# FL Studio Note Extraction Tool {VERSION}\n")
        f.write(f"# File: {os.path.basename(flp_path)}\n")
        f.write(f"# Tempo: {tempo} BPM\n")
        f.write(f"# PPQ: {ppq}\n")
        f.write("# Format: [start-end,pitch,instrument] dur=ticks vel=velocity\n\n")

        for pname, notes in raw_patterns.items():
            f.write(f"\n{'=' * 80}\n# Pattern: {pname}\n{'=' * 80}\n\n")
            for pos, key, dur, velocity, ch, ch_name in notes:
                s = calculate_fl_position(pos, ppq)
                e = calculate_fl_position(pos + dur, ppq)
                pn = get_pitch_name(key)
                f.write(f"[{s}-{e},{pn},{ch_name}] dur={dur}ticks vel={velocity}\n")

    print(f"[OK] All notes -> {all_path}")

    pdir = os.path.join(output_dir, "texts", "patterns")
    os.makedirs(pdir, exist_ok=True)
    count = 0
    for index, (pname, notes) in enumerate(raw_patterns.items(), start=1):
        safe = _indexed_stem(index, pname, f"NONAME{index:03d}")
        pp = os.path.join(pdir, f"{safe}.txt")
        with open(pp, "w", encoding="utf-8") as f:
            f.write(f"# Pattern: {pname}\n")
            for pos, key, dur, velocity, ch, ch_name in notes:
                s = calculate_fl_position(pos, ppq)
                e = calculate_fl_position(pos + dur, ppq)
                pn = get_pitch_name(key)
                f.write(f"[{s}-{e},{pn},{ch_name}] dur={dur}ticks vel={velocity}\n")
        print(f"[OK] Pattern {pname} -> {pp}")
        count += 1
    return count


def export_track_sequences(output_dir, flp_path, track_seqs, ppq):
    if not track_seqs:
        return 0
    texts_dir = os.path.join(output_dir, "texts")
    os.makedirs(texts_dir, exist_ok=True)
    path = os.path.join(texts_dir, "track_sequences.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# FL Studio Track Sequence Analysis {VERSION}\n")
        f.write(f"# File: {os.path.basename(flp_path)}\n")
        f.write(f"# Found {len(track_seqs)} track(s) with patterns\n\n")
        for tid, td in sorted(track_seqs.items(), key=lambda x: x[0]):
            f.write(f"### Track: {td['name']}\n")
            for ev in td["events"]:
                s = calculate_fl_position(ev["start"], ppq)
                e = calculate_fl_position(ev["end"], ppq)
                extra = ""
                if ev.get("offset_start") or ev.get("offset_end"):
                    extra = (
                        f" offset=start:{ev.get('offset_start', 0)}"
                        f"/end:{ev.get('offset_end', 0)}"
                    )
                f.write(
                    f"[{s}-{e}] {ev['pattern_name']} "
                    f"(dur={ev['length']}ticks{extra})\n"
                )
            f.write("\n")
    print(f"[OK] Track sequences -> {path}")
    return 1


# ---------------------------------------------------------------------------
# MIDI export
# ---------------------------------------------------------------------------

_NOTE_MAP = {
    "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3,
    "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8,
    "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11,
}


def _midi_note_number(key):
    """Convert a PyFLP key (int or 'C5' string) to MIDI note number 0-127."""
    if isinstance(key, int):
        return _clamp(key, 0, 127)
    key = str(key).strip()
    m = re.match(r"^([A-Ga-g]#?|[A-Ga-g]b)\s*(-?\d+)?$", key)
    if m:
        note = m.group(1).capitalize()
        octave = int(m.group(2)) if m.group(2) else 5
        base = _NOTE_MAP.get(note, 0)
        return _clamp(octave * 12 + base, 0, 127)
    try:
        return _clamp(int(key), 0, 127)
    except Exception:
        return 60


def _midi_velocity(value):
    """Convert FL/PyFLP note velocity to MIDI's 1-127 note-on range."""
    velocity = _safe_int(value, 100)
    return _clamp(velocity, 1, 127)


def _tempo_to_mido(tempo):
    tempo = float(tempo or 120.0)
    if tempo <= 0:
        tempo = 120.0
    return int(60_000_000 / tempo)


def _write_midi_track(mid, ch_id, ch_name, notes, ppq, tempo, midi_channel):
    """Append a MIDI track to mid (MidiFile) with given notes.
    notes: [(tick, key, dur, velocity), ...]
    midi_channel: 0-15 MIDI channel number
    """
    from mido import Message, MetaMessage, MidiTrack

    track = MidiTrack()
    track.append(MetaMessage("track_name", name=ch_name, time=0))

    events = []
    for pos, key, dur, velocity in notes:
        nn = _midi_note_number(key)
        vel = _midi_velocity(velocity)
        events.append((pos, "note_on", nn, vel))
        events.append((pos + dur, "note_off", nn, 0))
    # Note-off before note-on at the same tick avoids accidental overlaps.
    events.sort(key=lambda x: (x[0], 0 if x[1] == "note_off" else 1))

    last_tick = 0
    for tick, etype, nn, vel in events:
        delta = tick - last_tick
        if delta < 0:
            delta = 0
        if etype == "note_on":
            track.append(Message(
                "note_on",
                channel=midi_channel,
                note=nn,
                velocity=vel,
                time=delta,
            ))
        else:
            track.append(Message(
                "note_off",
                channel=midi_channel,
                note=nn,
                velocity=0,
                time=delta,
            ))
        last_tick = tick

    mid.tracks.append(track)


def _group_notes_by_channel(notes):
    groups = {}
    order = []
    for pos, key, dur, velocity, ch_id, ch_name in notes:
        if ch_id not in groups:
            groups[ch_id] = {"name": ch_name, "notes": []}
            order.append(ch_id)
        groups[ch_id]["notes"].append((pos, key, dur, velocity))
    try:
        ordered_ids = sorted(order)
    except TypeError:
        ordered_ids = order
    return OrderedDict((ch_id, groups[ch_id]) for ch_id in ordered_ids)


def _write_instrument_midi(path, ch_name, notes, tempo, ppq):
    from mido import MidiFile, MidiTrack, MetaMessage

    mid = MidiFile(ticks_per_beat=ppq)
    t0 = MidiTrack()
    mid.tracks.append(t0)
    t0.append(MetaMessage("set_tempo", tempo=_tempo_to_mido(tempo), time=0))
    _write_midi_track(mid, 0, ch_name, notes, ppq, tempo, 0)
    mid.save(path)


def export_pattern_midis(output_dir, raw_patterns, tempo, ppq):
    """Export one folder per pattern and one MIDI per active channel."""
    patterns_dir = os.path.join(output_dir, "patterns")
    os.makedirs(patterns_dir, exist_ok=True)

    midi_count = 0
    empty_patterns = []
    for p_index, (pname, notes) in enumerate(raw_patterns.items(), start=1):
        pdir_name = _indexed_stem(p_index, pname, f"NONAME{p_index:03d}")
        pdir = os.path.join(patterns_dir, pdir_name)
        os.makedirs(pdir, exist_ok=True)

        if not notes:
            empty_patterns.append(pdir_name)
            marker = os.path.join(pdir, "_EMPTY.txt")
            with open(marker, "w", encoding="utf-8") as f:
                f.write("This pattern contains no readable note data.\n")
                f.write("It may be empty, plugin-dependent, or unsupported by PyFLP.\n")
            print(f"[OK] Empty Pattern {pname} -> {pdir}")
            continue

        groups = _group_notes_by_channel(notes)
        for c_index, (ch_id, ch_data) in enumerate(groups.items(), start=1):
            cname = ch_data["name"]
            filename = _indexed_stem(
                c_index,
                cname,
                _channel_fallback(ch_id),
            )
            mpath = os.path.join(pdir, f"{filename}.mid")
            _write_instrument_midi(mpath, cname, ch_data["notes"], tempo, ppq)
            midi_count += 1
            print(f"[OK] Pattern MIDI {pname} / {cname} -> {mpath}")

    return {"midi_count": midi_count, "empty_patterns": empty_patterns}


def _place_note_on_playlist(note, event):
    """Place a Pattern note inside a Playlist clip's visible window."""
    pos, key, dur, velocity, ch_id, ch_name = note
    note_start = _safe_int(pos, 0)
    note_end = note_start + max(0, _safe_int(dur, 0))
    if note_end <= note_start:
        return None, False

    visible_start = max(0, _safe_int(event.get("offset_start", 0), 0))
    clip_length = _safe_int(event.get("length", 0), 0)
    visible_end = visible_start + clip_length if clip_length > 0 else None

    clipped_start = max(note_start, visible_start)
    clipped_end = note_end if visible_end is None else min(note_end, visible_end)
    if clipped_end <= clipped_start:
        return None, False

    out_pos = _safe_int(event.get("start", 0), 0) + (clipped_start - visible_start)
    out_dur = clipped_end - clipped_start
    placed = (out_pos, key, out_dur, velocity, ch_id, ch_name)
    clipped = clipped_start != note_start or clipped_end != note_end
    return placed, clipped


def export_track_midis(output_dir, raw_patterns, track_seqs, tempo, ppq):
    """Export one folder per Playlist Track and one MIDI per active channel."""
    tracks_dir = os.path.join(output_dir, "tracks")
    os.makedirs(tracks_dir, exist_ok=True)

    pnotes = {pname: notes for pname, notes in raw_patterns.items()}
    midi_count = 0
    skipped_tracks = []
    missing_patterns = []
    clipped_notes = 0
    placed_notes = 0

    for t_index, (tid, td) in enumerate(
        sorted(track_seqs.items(), key=lambda x: x[0]),
        start=1,
    ):
        track_notes = []
        for ev in td["events"]:
            pn = ev["pattern_name"]
            if pn not in pnotes:
                missing_patterns.append(f"{td['name']} / {pn}")
                continue
            for note in pnotes[pn]:
                placed, clipped = _place_note_on_playlist(note, ev)
                if placed is None:
                    continue
                track_notes.append(placed)
                placed_notes += 1
                if clipped:
                    clipped_notes += 1

        ch_all = _group_notes_by_channel(track_notes)
        if not ch_all:
            skipped_tracks.append(td["name"])
            continue

        tdir_name = _indexed_stem(t_index, td["name"], f"Track{tid}")
        tdir = os.path.join(tracks_dir, tdir_name)
        os.makedirs(tdir, exist_ok=True)

        for c_index, (ch_id, ch_data) in enumerate(ch_all.items(), start=1):
            cname = ch_data["name"]
            filename = _indexed_stem(
                c_index,
                cname,
                _channel_fallback(ch_id),
            )
            mpath = os.path.join(tdir, f"{filename}.mid")
            _write_instrument_midi(mpath, cname, ch_data["notes"], tempo, ppq)
            midi_count += 1
            print(f"[OK] Track MIDI {td['name']} / {cname} -> {mpath}")

    return {
        "midi_count": midi_count,
        "skipped_tracks": skipped_tracks,
        "missing_patterns": missing_patterns,
        "clipped_notes": clipped_notes,
        "placed_notes": placed_notes,
    }


def export_summary(
    output_dir,
    flp_path,
    tempo,
    ppq,
    raw_patterns,
    total_notes,
    track_seqs,
    text_stats,
    pattern_stats,
    track_stats,
    note_stats,
    playlist_stats,
):
    path = os.path.join(output_dir, "summary.txt")
    channel_names = OrderedDict()
    for notes in raw_patterns.values():
        for pos, key, dur, velocity, ch_id, ch_name in notes:
            channel_names[ch_id] = ch_name

    with open(path, "w", encoding="utf-8") as f:
        f.write(f"FlpInfoer {VERSION} Export Summary\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"File: {os.path.basename(flp_path)}\n")
        f.write(f"Output: {output_dir}\n")
        f.write(f"Tempo: {tempo} BPM\n")
        f.write(f"PPQ: {ppq}\n\n")

        f.write("Counts\n")
        f.write("-" * 20 + "\n")
        f.write(f"Patterns: {len(raw_patterns)}\n")
        f.write(f"Playlist tracks with pattern clips: {len(track_seqs)}\n")
        f.write(f"Readable notes: {total_notes}\n")
        f.write(f"Active channels in notes: {len(channel_names)}\n")
        f.write(f"Pattern MIDI files: {pattern_stats['midi_count']}\n")
        f.write(f"Track MIDI files: {track_stats['midi_count']}\n")
        f.write(f"Pattern text files: {text_stats['pattern_text_count']}\n\n")

        f.write("Channels\n")
        f.write("-" * 20 + "\n")
        if channel_names:
            for index, ch_id in enumerate(sorted(channel_names), start=1):
                name = channel_names[ch_id]
                f.write(f"{index:03d}. id={ch_id} name={name}\n")
        else:
            f.write("(none)\n")
        f.write("\n")

        f.write("Disabled Channels\n")
        f.write("-" * 20 + "\n")
        disabled_channels = note_stats.get("disabled_channels", {})
        if disabled_channels:
            for ch_id, name in disabled_channels.items():
                f.write(f"- id={ch_id} name={name}\n")
            f.write(
                f"Skipped notes on disabled channels: "
                f"{note_stats.get('skipped_disabled_notes', 0)}\n"
            )
        else:
            f.write("(none)\n")
        f.write("\n")

        f.write("Empty Patterns\n")
        f.write("-" * 20 + "\n")
        if pattern_stats["empty_patterns"]:
            for name in pattern_stats["empty_patterns"]:
                f.write(f"- {name}\n")
        else:
            f.write("(none)\n")
        f.write("\n")

        f.write("Skipped Playlist Tracks\n")
        f.write("-" * 20 + "\n")
        if track_stats["skipped_tracks"]:
            for name in track_stats["skipped_tracks"]:
                f.write(f"- {name}\n")
        else:
            f.write("(none)\n")
        f.write("\n")

        f.write("Skipped Playlist Items\n")
        f.write("-" * 20 + "\n")
        wrote_skip = False
        if playlist_stats.get("skipped_disabled_tracks"):
            wrote_skip = True
            f.write("Disabled tracks:\n")
            for name in playlist_stats["skipped_disabled_tracks"]:
                f.write(f"- {name}\n")
        if playlist_stats.get("skipped_muted_items"):
            wrote_skip = True
            f.write("Muted pattern clips:\n")
            for name in playlist_stats["skipped_muted_items"]:
                f.write(f"- {name}\n")
        if playlist_stats.get("unsupported_items"):
            wrote_skip = True
            f.write("Unsupported non-pattern playlist items:\n")
            for name in playlist_stats["unsupported_items"]:
                f.write(f"- {name}\n")
        if track_stats.get("missing_patterns"):
            wrote_skip = True
            f.write("Missing pattern references:\n")
            for name in track_stats["missing_patterns"]:
                f.write(f"- {name}\n")
        if not wrote_skip:
            f.write("(none)\n")
        f.write("\n")

        f.write("Clip Trimming and Offsets\n")
        f.write("-" * 20 + "\n")
        f.write(f"Playlist notes placed: {track_stats.get('placed_notes', 0)}\n")
        f.write(f"Notes clipped by Playlist item bounds: {track_stats.get('clipped_notes', 0)}\n")
        if playlist_stats.get("offset_items"):
            f.write("Items with offsets:\n")
            for name in playlist_stats["offset_items"]:
                f.write(f"- {name}\n")
        else:
            f.write("Items with offsets: (none)\n")
        f.write("\n")

        f.write("Notes\n")
        f.write("-" * 20 + "\n")
        f.write("V0.5 skips disabled channels, disabled Playlist tracks, and muted Pattern clips.\n")
        f.write("Track MIDI placement respects Playlist clip length and start offsets when PyFLP exposes them.\n")
        f.write("Audio clips, automation clips, plugin sounds, mixer effects, and full playback state are still outside this MIDI-only scope.\n")

    print(f"[OK] Summary -> {path}")
    return path


def export_project(
    flp_path,
    raw_patterns,
    tempo,
    ppq,
    total_notes,
    track_seqs,
    note_stats,
    playlist_stats,
):
    output_dir = _prepare_output_dir(flp_path)
    print(f"\nOutput folder: {output_dir}")

    text_count = export_results(output_dir, flp_path, raw_patterns, tempo, ppq)
    export_track_sequences(output_dir, flp_path, track_seqs, ppq)

    print("\n--- Pattern Instrument MIDI ---")
    pattern_stats = export_pattern_midis(output_dir, raw_patterns, tempo, ppq)

    print("\n--- Playlist Track Instrument MIDI ---")
    track_stats = export_track_midis(output_dir, raw_patterns, track_seqs, tempo, ppq)

    text_stats = {"pattern_text_count": text_count}
    export_summary(
        output_dir,
        flp_path,
        tempo,
        ppq,
        raw_patterns,
        total_notes,
        track_seqs,
        text_stats,
        pattern_stats,
        track_stats,
        note_stats,
        playlist_stats,
    )
    return output_dir


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def extract_flp_notes(flp_path):
    from pyflp import parse

    print(f"\n{'=' * 50}")
    print(f"FlpInfoer {VERSION}")
    print(f"{'=' * 50}\n")
    print(f"Analyzing: {os.path.basename(flp_path)}")

    t0 = time.time()

    try:
        print("Loading...")
        project = parse(flp_path)
        ppq = _safe_getattr(project, "ppq", 96)
        tempo = _safe_getattr(project, "tempo", 120.0)
        print(f"Loaded  Tempo={tempo} BPM  PPQ={ppq}")

        channel_info = create_channel_info(project)

        print("\nParsing notes...")
        _, _, raw_patterns, total, pattern_labels_by_iid, note_stats = _consume_pattern_notes(
            project,
            channel_info,
        )
        print(f"Found {total} notes in {len(raw_patterns)} pattern(s)")

        print("\n--- Playlist ---")
        track_seqs, playlist_stats = parse_playlist(project, pattern_labels_by_iid)

        print("\n--- Export ---")
        export_project(
            flp_path,
            raw_patterns,
            tempo,
            ppq,
            total,
            track_seqs,
            note_stats,
            playlist_stats,
        )

        print(f"\n{'=' * 50}")
        print("All done!")
        ok = True

    except Exception as e:
        print(f"\nError: {e}")
        traceback.print_exc()
        ok = False

    print(f"Time: {time.time() - t0:.2f}s")
    return ok


def main():
    _fix_stdout()
    print(f"FL Studio Note Extraction Tool {VERSION}")

    if not _check_python_version():
        print("\nPress Enter to exit...")
        try:
            input()
        except (EOFError, OSError):
            pass
        return 1

    if len(sys.argv) < 2:
        print("\nDrag .flp file here or enter path: ", end="")
        flp_path = input().strip('"')
    else:
        flp_path = sys.argv[1]

    flp_path = flp_path.strip('"')

    if not os.path.isfile(flp_path):
        print(f"\nError: file not found: {flp_path}")
        print("\nPress Enter to exit...")
        try:
            input()
        except (EOFError, OSError):
            pass
        return 1

    sys.setrecursionlimit(10000)

    if not flp_path.lower().endswith(".flp"):
        print(f"\nWarning: not a .flp file: {flp_path}")

    ok = extract_flp_notes(flp_path)
    print("\nPress Enter to exit...")
    try:
        input()
    except (EOFError, OSError):
        pass
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
