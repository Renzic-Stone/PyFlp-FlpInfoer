# Release Notes

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
