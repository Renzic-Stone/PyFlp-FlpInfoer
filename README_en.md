# FlpInfoer
([中文](https://github.com/Renzic-Stone/PyFlp-FlpInfoer/blob/main/README.md) / [日本語](https://github.com/Renzic-Stone/PyFlp-FlpInfoer/blob/main/README_jp.md))

FlpInfoer is a third-party FL Studio `.flp` MIDI extraction tool based on Python 3.10, [PyFLP](https://github.com/demberto/PyFLP) v2.2.1, and [mido](https://github.com/mido/mido).

The goal is not to fully convert an FL Studio project. FlpInfoer focuses on rescuing MIDI data from `.flp` files for DAW migration, collaboration, external vocal-synthesis workflows such as Vocaloid or SynthV, and cases where plugins are missing or too heavy to load.

## Current Features
1. Export all notes grouped by Pattern
2. Export per-Pattern text note files
3. Export BPM and PPQ
4. Export `.mid` files per Pattern
5. Export full-timeline `.mid` files per Playlist Track, with instrument-named MIDI tracks inside
6. Export Playlist Track Pattern sequences
7. Preserve note velocity read by PyFLP
8. Preserve actual playback pitch instead of matching octave display names across DAWs

## Requirements
- Python 3.10
- PyFLP 2.2.1
- mido 1.3+

PyFLP 2.2.1 may fail to import or parse on Python 3.11 or newer because of Enum compatibility issues. This project is currently maintained and tested against Python 3.10.

```bash
py -3.10 -m pip install -r requirements.txt
py -3.10 FlpInfoer.py "your project.flp"
```

You can also run the script and drag the `.flp` path into the console window.

## Current Output
For `Song.flp`, the current version generates:

```text
Song_all_notes.txt
Song_patterns/
Song_track_sequences.txt
Song_midi_patterns/
Song_midi_tracks/
```

A future version is planned to use a migration-friendly folder layout that splits Pattern and Playlist Track exports further by active instrument.

## Format and Positioning
Text note format:

```text
[start_bar:step:tick-end_bar:step:tick,pitch,instrument] dur=ticks vel=velocity
```

Position format: bar (1-based) : step (00-15) : tick.
When PPQ is 96, each sixteenth-note step is 24 ticks. With other PPQ values, the tick range changes with PPQ.

## MIDI Pitch Policy
MIDI files store note numbers, not display names such as `C4` or `C5`. Different DAWs may show different octave names for the same note number.

FlpInfoer preserves the actual FL Studio / PyFLP playback pitch by default. It does not automatically transpose notes just to make another DAW show the same octave label.

## Scope
FlpInfoer currently extracts MIDI-related information such as notes, tempo, Patterns, Pattern positions on Playlist Tracks, and instrument names. It does not export or recreate plugin sounds, mixer effects, audio, automation, or the complete playback state of a project.

> Note: This project is not affiliated with [FL Studio](https://www.image-line.com/fl-studio/) or [FlpInfo](https://github.com/demberto/FLPInfo). FlpInfo also depends on PyFLP but is no longer maintained.

## License
**Code**: Licensed under GPL-3.0 for free use, modification, and distribution.

**Assets**: Icons that may be bundled with official `.exe` releases are original designs by Renzic_Stone and remain copyrighted. Unless explicitly stated otherwise, those icons are not licensed under GPL-3.0 or any other open-source software license.

- Official icon-bundled releases may be redistributed for non-commercial purposes with attribution
- Commercial sale, paid download, or VIP-only distribution of the icon or official icon-bundled release requires permission
- For commercial licensing, contact [Renzic-Stone](https://github.com/Renzic-Stone) or rzs_@outlook.com

Builds made from the GPL-3.0 source code with the non-GPL icon removed or replaced may be distributed under GPL-3.0 terms.

## AI Assistance
Parts of this project were assisted by generative AI. All content has been reviewed, verified, and modified by the author.

## Contact
- Maintainer: Renzic-Stone
- Email: rzs_@outlook.com
