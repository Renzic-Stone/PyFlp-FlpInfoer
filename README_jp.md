# FlpInfoer
([English README](https://github.com/Renzic-Stone/PyFlp-FlpInfoer/blob/main/README_en.md) / [中文说明](https://github.com/Renzic-Stone/PyFlp-FlpInfoer/blob/main/README.md))

Python 3.10 と [PyFlp](https://github.com/demberto/PyFLP) v2.2.1 + [mido](https://github.com/mido/mido) を使用して FL Studio の .flp プロジェクトファイルを解析・MIDI 出力するサードパーティーツールです。

### 現在の機能
1. 全ノートのエクスポート（Pattern ごとにグループ化） ✅
2. Pattern 別ノートファイル出力 ✅
3. テンポ（BPM）出力 ✅
4. Pattern 別 .mid 出力 ✅
5. トラック別完全楽曲 .mid 出力（楽器名付きトラック分け） ✅
6. プレイリストのトラックシーケンス出力 ✅

### フォーマットと位置
**ノート形式:** `[開始小節:ステップ:ティック-終了小節:ステップ:ティック, 音高, 楽器名]`（継続=ticks）
**位置:** 小節（1開始）: ステップ（00-15, 16進数）: ティック（00-23, 24進数）

FL Studio の MIDI エクスポート機能の欠点（楽器別トラック分け不可、Pattern 一括出力不可）を解決します。

> 注意: [FL Studio](https://www.image-line.com/fl-studio/) および [FlpInfo](https://github.com/demberto/FLPInfo) とは無関係です（後者は PyFlp を使用していますが更新停止中）。全コードはオリジナルまたは AI 生成後に手動修正したものです。

## ライセンス
**コード:** GPL-3.0（自由な使用・改変・配布が可能）
**アセット:** 同梱 .exe のアイコンは Renzic_Stone がデザインし、著作権を保有します:
- ✅ 非商用配布は自由（ブログ・クラウドストレージ）
- ❌ 商用利用禁止（有料ダウンロード・VIP コンテンツ・販売）
- 📮 商用ライセンス: [Renzic-Stone](https://github.com/Renzic-Stone) | rzs_@outlook.com

### AI 支援について
一部は生成 AI（ChatGPT など）によって開発されました。すべての出力は著者によって検証・修正されています。

---

## 連絡先
問題があれば GitHub またはメールでご連絡ください:
- メンテナー: [Renzic-Stone](https://github.com/Renzic-Stone)
- メール: rzs_@outlook.com
