# FlpInfoer
([English](https://github.com/Renzic-Stone/PyFlp-FlpInfoer/blob/main/README_en.md) / [中文](https://github.com/Renzic-Stone/PyFlp-FlpInfoer/blob/main/README.md))

FlpInfoer は、Python 3.10、[PyFLP](https://github.com/demberto/PyFLP) v2.2.1、[mido](https://github.com/mido/mido) を使用して FL Studio の `.flp` から MIDI 情報を抽出するサードパーティーツールです。

このプロジェクトの目的は FL Studio プロジェクトを完全変換することではありません。DAW 移行、共同制作、Vocaloid / SynthV などの外部ボーカル制作環境、プラグイン不足や PC 性能不足でプロジェクトを開きにくい場合に、`.flp` 内の MIDI データをできるだけ実用的に救出することを目的としています。

## 現在の機能
1. 全ノートを Pattern ごとにグループ化して出力
2. Pattern 別のテキストノート出力
3. BPM と PPQ の出力
4. Pattern ごとにフォルダを作成し、実際にノートがある楽器ごとに `.mid` を出力
5. Playlist Track ごとにフォルダを作成し、タイムライン上の Pattern を結合して楽器ごとに `.mid` を出力
6. Playlist Track 上の Pattern シーケンス出力
7. PyFLP から読み取った note velocity の保持
8. DAW 間のオクターブ表示名ではなく、実際の再生音高を保持
9. Playlist Track MIDI で clip length と start offset によるノートのトリミング/オフセットを反映
10. disabled Channel、disabled Playlist Track、muted Pattern clip をスキップ
11. スキップされた track / clip / 非 Pattern item とトリミング統計を `summary.txt` に記録

## 必要環境
- Python 3.10
- PyFLP 2.2.1
- mido 1.3+

PyFLP 2.2.1 は Python 3.11 以降で Enum 互換性の問題により import や解析に失敗する場合があります。このプロジェクトは現在 Python 3.10 を対象に保守・検証しています。

```bash
py -3.10 -m pip install -r requirements.txt
py -3.10 FlpInfoer.py "your project.flp"
```

スクリプトを起動して、コンソールウィンドウへ `.flp` のパスをドラッグすることもできます。

## 現在の出力
`Song.flp` の場合、現在のバージョンはプログラムと同じ場所に以下のフォルダを生成します。

```text
Song/
  all_notes.txt
  summary.txt
  texts/
    track_sequences.txt
    patterns/
      001 - PatternName.txt
      002 - NONAME002.txt
  patterns/
    001 - PatternName/
      001 - InstrumentName.mid
    002 - NONAME002/
      _EMPTY.txt
  tracks/
    001 - Track1/
      001 - InstrumentName.mid
```

同名の出力フォルダが既に存在する場合、FlpInfoer は古いフォルダを削除して再生成します。名前のない Pattern は `NONAME001` のような名前になり、名前のない Channel は `NONAME_Channel001` のような名前になります。空の Pattern は `_EMPTY.txt` 付きのフォルダとして保持し、空の Channel と空の Playlist Track は生成しません。

## フォーマットと位置
テキストノート形式:

```text
[開始小節:ステップ:ティック-終了小節:ステップ:ティック,音高,楽器名] dur=ticks vel=velocity
```

位置形式は、小節（1 始まり）: ステップ（00-15）: ティックです。
PPQ が 96 の場合、16 分音符 1 ステップは 24 tick です。その他の PPQ では、ティック範囲は PPQ に応じて変わります。

## MIDI 音高方針
MIDI ファイルは note number を保存し、`C4` / `C5` のような表示名は保存しません。同じ note number でも DAW によってオクターブ表示が異なる場合があります。

FlpInfoer はデフォルトで FL Studio / PyFLP 上の実際の再生音高を保持します。他の DAW で同じオクターブ名を表示させるための自動移調は行いません。

## 範囲
FlpInfoer が現在抽出するのは、ノート、テンポ、Pattern、Playlist Track 上の Pattern 位置、楽器名などの MIDI 関連情報です。V0.5 では Playlist Track MIDI を実際に聴こえる状態へ近づけるため、disabled Channel、disabled Playlist Track、muted Pattern clip をスキップし、clip length と start offset をタイムライン配置に反映します。

それでも、プラグイン音色、ミキサーエフェクト、音声、オートメーション、プロジェクト全体の再生状態は出力・再現しません。Audio clip、automation clip などの非 Pattern プレイリスト項目は MIDI に変換せず、`summary.txt` で unsupported として記録します。

> 注意: このプロジェクトは [FL Studio](https://www.image-line.com/fl-studio/) および [FlpInfo](https://github.com/demberto/FLPInfo) とは無関係です。FlpInfo も PyFLP に依存していますが、現在は保守されていません。

## ライセンス
**コード**: GPL-3.0 license の下で、自由に使用・改変・配布できます。

**アセット**: 公式 `.exe` リリースに同梱される場合があるアイコンは Renzic_Stone によるオリジナルデザインであり、著作権は保持されています。明示されていない限り、これらのアイコンは GPL-3.0 またはその他のオープンソースソフトウェアライセンスの対象ではありません。

- アイコン付き公式リリースは、作者表記を残した上で非商用配布できます
- アイコンまたはアイコン付き公式リリースの商用販売、有料ダウンロード、VIP 限定配布には許可が必要です
- 商用ライセンスについては [Renzic-Stone](https://github.com/Renzic-Stone) または rzs_@outlook.com までご連絡ください

GPL-3.0 のソースコードから非 GPL アイコンを削除または置換してビルドしたものは、GPL-3.0 の条件で配布できます。

## AI 支援について
本プロジェクトの一部は生成 AI の支援を受けています。すべての内容は作者によって確認・検証・修正されています。

## 連絡先
- メンテナー: Renzic-Stone
- メール: rzs_@outlook.com
