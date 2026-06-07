# FlpInfoer
([中文](https://github.com/Renzic-Stone/PyFlp-FlpInfoer/blob/main/README.md) / [日本語](https://github.com/Renzic-Stone/PyFlp-FlpInfoer/blob/main/README_jp.md))

A Python 3.10-based tool using [PyFlp](https://github.com/demberto/PyFLP) v2.2.1 + [mido](https://github.com/mido/mido) to parse & export FL Studio project files (.flp) to MIDI.

### Current Features
1. Export all notes (grouped by Pattern) ✅
2. Export notes per Pattern file ✅
3. Export tempo (BPM) ✅
4. Export .mid files per Pattern ✅
5. Export full-song .mid with instrument-named tracks ✅
6. Export playlist track sequences ✅

### Format & Positioning
**Note format:** `[start_bar:step:tick - end_bar:step:tick, pitch, instrument] (duration=ticks)`
**Positioning:** Bar (1-based) : Step (00-15, hex) : Tick (00-23, 24ppq)
*(Matches FL Studio Piano Roll internal indexing)*

**Solves FL Studio's MIDI export limitations**:
* No per-track instrument mapping
* No batch Pattern export

> ⚠️ **Important Disclaimers**
> * Not affiliated with [FL Studio](https://www.image-line.com/fl-studio/) or [FlpInfo](https://github.com/demberto/FLPInfo) (which uses PyFlp but is discontinued)
> * All code is original or AI-generated then manually rewritten

## License
**Code**: Licensed under GPL-3.0 (free use/modification/distribution)
**Assets**: Bundled .exe icons designed by Renzic_Stone are **copyrighted**:
- ✅ Free for non-commercial distribution (blogs/cloud storage)
- ❌ Commercial use prohibited (paid downloads/VIP content/sales)
- 📮 Commercial licensing: Contact [Renzic-Stone](https://github.com/Renzic-Stone) | rzs_@outlook.com

### AI Assistance Note
Partially developed with generative AI (e.g. ChatGPT). All output has been validated, modified, and curated by the author.

---

## Contact
Report issues via GitHub or email:
- Maintainer: [Renzic-Stone](https://github.com/Renzic-Stone)
- Email: rzs_@outlook.com
