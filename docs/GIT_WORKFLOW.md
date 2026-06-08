# Git Workflow

This project keeps Git lightweight. `main` is the release line, and day-to-day work should happen on local working branches.

## Branches

- `main`: release-ready code only. Tags such as `V0.3.2` point here.
- `dev`: local integration branch for the next version.
- `work/<version>-<topic>`: temporary feature or fix branches, for example `work/v0.4-export-layout`.

`dev` does not need to be pushed unless collaboration needs it. GitHub releases should be cut from `main`.

## Local Setup

The repository should use local identity settings, not global machine settings:

```bash
git config user.name "Renzic-Stone"
git config user.email "rzs_@outlook.com"
git config core.autocrlf false
git config core.eol lf
```

`.gitattributes` keeps source and docs as LF text files, and treats `.exe`, `.ico`, `.flp`, and `.mid` as binary files.

## Development Flow

Start new work from the current release state:

```bash
git switch main
git pull --ff-only origin main
git switch -C dev main
git switch -c work/v0.4-export-layout
```

Commit in small, named steps:

```bash
git status --short
git add <files>
git commit -m "V0.4: add export layout model"
```

Merge back locally when the feature is verified:

```bash
git switch dev
git merge --ff-only work/v0.4-export-layout
```

## Verification Before Release

Run at least:

```bash
py -3.10 -m py_compile FlpInfoer.py
py -3.10 FlpInfoer.py "D:/Reasonix/测试.flp"
py -3.10 -m PyInstaller FlpInfoer.spec --clean --noconfirm
```

For the current sample project, confirm:

- tempo is `130`
- total note count is `47`
- Playlist pattern item count is `6`
- Pattern `1.mid` exports note `60` for the drum channels
- Pattern `2.mid` exports notes `53`, `55`, `57`, and `59`

## Release Flow

Before tagging:

- update `VERSION` in `FlpInfoer.py`
- update `README.md`, `README_en.md`, and `README_jp.md`
- update `RELEASE_NOTES.md`
- build and test `dist/FlpInfoer.exe`

Release from `main`:

```bash
git switch main
git merge --ff-only dev
git push origin main
git tag V0.x.y
git push origin V0.x.y
gh release create V0.x.y "dist/FlpInfoer.exe" --repo Renzic-Stone/PyFlp-FlpInfoer --title "V0.x.y" --notes-file RELEASE_NOTES.md
```

Keep generated folders such as `build/`, `dist/`, and validation output out of Git. Upload the verified `.exe` as a GitHub Release asset instead.
