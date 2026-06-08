# Release Notes

## V0.5.0

### 中文
- Playlist Track MIDI 拼接现在会按 Pattern clip 的可见长度裁剪音符。
- 支持 Pattern clip 的 start offset：左侧裁剪后的 clip 会把音符放到正确的轨道时间位置。
- 跳过 disabled Channel、disabled Playlist Track 和 muted Pattern clip，使导出的轨道 MIDI 更接近实际可听状态。
- 对 PyFLP 中可能缺失的 `muted`、`offsets`、`enabled` 等字段改用安全读取，减少真实工程里的异常中断。
- `summary.txt` 新增 disabled Channel、跳过的 Playlist 项目、非 Pattern 项目、offset 项目和裁剪统计。
- 更新中文、英文、日文 README，说明 V0.5 能力和仍不处理的音频、自动化、插件、混音台边界。

### English
- Playlist Track MIDI placement now trims notes by the visible length of each Pattern clip.
- Pattern clip start offsets are respected, so left-trimmed clips place notes at the correct track timeline positions.
- Disabled Channels, disabled Playlist Tracks, and muted Pattern clips are skipped so track MIDI is closer to the audible project state.
- PyFLP fields that may be absent, such as `muted`, `offsets`, and `enabled`, are now read safely to reduce crashes on real projects.
- `summary.txt` now reports disabled Channels, skipped Playlist items, unsupported non-Pattern items, offset items, and trimming stats.
- Updated Chinese, English, and Japanese READMEs with the V0.5 behavior and the remaining audio, automation, plugin, and mixer boundaries.

### 日本語
- Playlist Track MIDI の配置で、各 Pattern clip の可視長に合わせてノートをトリミングするようにしました。
- Pattern clip の start offset に対応し、左側がトリミングされた clip でも正しいトラック時間位置にノートを配置します。
- disabled Channel、disabled Playlist Track、muted Pattern clip をスキップし、トラック MIDI を実際に聴こえる状態へ近づけました。
- PyFLP で存在しない場合がある `muted`、`offsets`、`enabled` などのフィールドを安全に読み取り、実プロジェクトでの異常終了を減らしました。
- `summary.txt` に disabled Channel、スキップされた Playlist item、非 Pattern item、offset item、トリミング統計を追加しました。
- 中国語・英語・日本語 README を更新し、V0.5 の挙動と、引き続き対象外である音声・オートメーション・プラグイン・ミキサーの範囲を説明しました。

## V0.4.0

### 中文
- 新增迁移友好的输出目录：每个 `.flp` 会导出到程序所在目录下的同名文件夹。
- Pattern 导出改为每个 Pattern 一个文件夹，并按实际有音符的 Channel / 乐器拆分为独立 `.mid`。
- Playlist Track 导出改为每个轨道一个文件夹，按 Pattern clip 的实际位置拼接后再按乐器拆分为独立 `.mid`。
- 文本输出整理到 `texts/`，根目录保留 `all_notes.txt` 和 `summary.txt`。
- 每个单独的乐器 MIDI 文件都写入 tempo meta track，方便导入其他 DAW 或人声合成软件。
- 无名 Pattern 使用 `NONAME001` 风格命名，无名 Channel 使用 `NONAME_Channel001` 风格命名。
- 空 Pattern 会保留文件夹并写入 `_EMPTY.txt`；空 Channel 和空 Playlist Track 不生成文件。
- 更新中文、英文、日文 README，说明 V0.4 输出结构和当前边界。

### English
- Added a migration-friendly output folder: each `.flp` exports into a same-named folder next to the program.
- Pattern export now creates one folder per Pattern and splits active Channels / instruments into separate `.mid` files.
- Playlist Track export now creates one folder per track, places Pattern clips by their timeline positions, and splits the merged result by instrument.
- Text outputs are organized under `texts/`, while `all_notes.txt` and `summary.txt` stay in the root output folder.
- Each single-instrument MIDI file includes a tempo meta track for DAW and vocal-synthesis imports.
- Unnamed Patterns use names such as `NONAME001`; unnamed Channels use names such as `NONAME_Channel001`.
- Empty Patterns keep a folder with `_EMPTY.txt`; empty Channels and empty Playlist Tracks are not generated.
- Updated Chinese, English, and Japanese READMEs with the V0.4 output layout and current scope.

### 日本語
- 移行向けの出力フォルダ構成を追加しました。各 `.flp` はプログラムと同じ場所の同名フォルダへ出力されます。
- Pattern 出力は Pattern ごとのフォルダを作成し、実際にノートがある Channel / 楽器を個別の `.mid` として出力します。
- Playlist Track 出力はトラックごとのフォルダを作成し、Pattern clip のタイムライン位置に従って結合した上で、楽器ごとに `.mid` を出力します。
- テキスト出力は `texts/` に整理し、ルートには `all_notes.txt` と `summary.txt` を残します。
- 各単一楽器 MIDI ファイルには tempo meta track を含め、DAW やボーカル制作ソフトへ読み込みやすくしました。
- 名前のない Pattern は `NONAME001`、名前のない Channel は `NONAME_Channel001` のように命名します。
- 空の Pattern は `_EMPTY.txt` 付きのフォルダとして保持し、空の Channel と空の Playlist Track は生成しません。
- 中国語・英語・日本語 README を更新し、V0.4 の出力構成と現在の範囲を説明しました。

## V0.3.2

### 中文
- 修正 MIDI 音高策略：默认保持 FL Studio / PyFLP 的实际播放音高，不再为了八度显示名自动升高八度。
- MIDI 导出现在保留 PyFLP 读取到的 note velocity。
- 明确 Python 3.10 要求，并在其他 Python 版本下给出清楚提示。
- 改进 Pattern、Track、Channel 文件名的安全处理，减少非法字符和重名覆盖风险。
- Playlist 解析改用 PyFLP 的 `arrangement.tracks` 高层入口，减少对内部事件结构的依赖。
- 更新中文、英文、日文 README，补充项目定位、MIDI 音高说明、当前边界和许可证说明。

### English
- Fixed the MIDI pitch policy: exports now preserve the actual FL Studio / PyFLP playback pitch instead of shifting notes to match octave display names.
- MIDI export now preserves note velocity read by PyFLP.
- Clarified the Python 3.10 requirement and added a clear warning for other Python versions.
- Improved filename safety for Pattern, Track, and Channel names to reduce invalid-character and duplicate-name issues.
- Playlist parsing now uses PyFLP's high-level `arrangement.tracks` API instead of relying on internal event structures.
- Updated Chinese, English, and Japanese READMEs with clearer positioning, MIDI pitch notes, scope, and license wording.

### 日本語
- MIDI 音高方針を修正し、オクターブ表示名に合わせるための自動移調ではなく、FL Studio / PyFLP の実際の再生音高を保持するようにしました。
- MIDI 出力で PyFLP から読み取った note velocity を保持するようにしました。
- Python 3.10 要件を明確化し、その他の Python バージョンでは分かりやすい警告を表示します。
- Pattern、Track、Channel 名のファイル名安全処理を改善し、無効文字や重複名による上書きリスクを減らしました。
- Playlist 解析を PyFLP の高レベル `arrangement.tracks` API に変更し、内部イベント構造への依存を減らしました。
- 中国語・英語・日本語 README を更新し、プロジェクトの位置付け、MIDI 音高方針、範囲、ライセンス説明を明確化しました。
