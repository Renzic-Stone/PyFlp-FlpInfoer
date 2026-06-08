# FlpInfoer
([English](https://github.com/Renzic-Stone/PyFlp-FlpInfoer/blob/main/README_en.md) / [日本語](https://github.com/Renzic-Stone/PyFlp-FlpInfoer/blob/main/README_jp.md))

FlpInfoer 是一个基于 Python 3.10、[PyFLP](https://github.com/demberto/PyFLP) v2.2.1 和 [mido](https://github.com/mido/mido) 的第三方 FL Studio `.flp` MIDI 提取工具。

本项目的目标不是完整转换 FL Studio 工程，而是把 `.flp` 中的 MIDI 信息尽量可靠地救出来，方便 DAW 迁移、跨软件协作、Vocaloid/SynthV 等外部人声工作流，以及缺少插件或电脑性能不足时的 MIDI 中介导出。

## 目前已经实现的功能
1. 导出所有音符，并按 Pattern 分组
2. 按 Pattern 分文件导出文本音符
3. 导出速度 BPM 和 PPQ
4. 按 Pattern 建文件夹，并按实际有音符的乐器分别导出 `.mid`
5. 按 Playlist Track 建文件夹，并按该轨道时间线拼接后按乐器分别导出 `.mid`
6. 导出播放列表轨道上的 Pattern 序列
7. 保留 PyFLP 读取到的 note velocity
8. 保持实际 MIDI 音高听感，不追求跨 DAW 的八度显示名一致
9. Playlist Track MIDI 会按 clip length 和 start offset 裁剪/偏移音符
10. 跳过 disabled Channel、disabled Playlist Track 和 muted Pattern clip
11. 在 `summary.txt` 中记录被跳过的轨道、clip、非 Pattern 项目和裁剪统计

## 使用要求
- Python 3.10
- PyFLP 2.2.1
- mido 1.3+

PyFLP 2.2.1 在 Python 3.11 或更新版本上可能因 Enum 兼容性问题无法正常导入或解析。本项目当前按 Python 3.10 维护和测试。

```bash
py -3.10 -m pip install -r requirements.txt
py -3.10 FlpInfoer.py "你的工程.flp"
```

也可以运行脚本后把 `.flp` 路径拖入窗口。

## 当前输出
以 `Song.flp` 为例，当前版本会在程序所在目录生成：

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

如果同名输出目录已存在，FlpInfoer 会删除旧目录并重新生成。无名 Pattern 会使用 `NONAME001` 这类名称；无名 Channel 会使用 `NONAME_Channel001` 这类名称。空 Pattern 会保留文件夹并写入 `_EMPTY.txt`，空 Channel 和空 Playlist Track 不生成文件。

## 格式与位置
文本音符格式：

```text
[开始小节:步:嘀嗒-结束小节:步:嘀嗒,音高,乐器名] dur=ticks vel=velocity
```

位置格式为：小节（1 开始）: 步（00-15）: 嘀嗒。
当 PPQ 为 96 时，每个十六分步为 24 tick；其他 PPQ 下嘀嗒范围会随 PPQ 改变。

## MIDI 音高说明
MIDI 文件只保存 note number，不保存 `C4` / `C5` 这类显示名。不同 DAW 对同一个 note number 的八度显示可能不同。

FlpInfoer 默认以听感和可回收性为准：保留 FL Studio / PyFLP 中的实际音高，不为了让其他 DAW 显示相同的八度名而自动移调。

## 边界
本工具目前只提取 MIDI 相关信息，例如音符、速度、Pattern、Playlist Track 中的 Pattern 位置和乐器名。V0.5 会尽量让 Playlist Track MIDI 接近实际可听状态：disabled Channel、disabled Playlist Track 和 muted Pattern clip 会被跳过，clip length 与 start offset 会参与轨道拼接。

它仍然不会导出或还原插件音色、混音台效果、音频、自动化，或工程里的完整播放状态。音频 clip、自动化 clip 等非 Pattern 播放列表项目会在 `summary.txt` 中标记为 unsupported，而不是转换为 MIDI。

> 注意：本项目与 [FL Studio](https://www.image-line.com/fl-studio/) 和 [FlpInfo](https://github.com/demberto/FLPInfo) 无关。后者同样依赖 PyFLP，但已停止更新。

## 许可证
**代码**：使用 GPL-3.0 license 授权，允许自由使用、修改与分发。

**资产**：官方发行版中可能附带的 `.exe` 图标由 Renzic_Stone 原创设计并保留版权。除非另有明确说明，该图标不适用于 GPL-3.0 或其他开源软件许可证。

- 可在非商业用途下自由分发带图标的官方发行包，需保留作者署名
- 未经授权不得将该图标或带该图标的官方发行包用于商业销售、付费下载或 VIP 内容
- 如需商业授权，请联系 [Renzic-Stone](https://github.com/Renzic-Stone) 或 rzs_@outlook.com

自行从 GPL-3.0 源码构建并移除或替换非 GPL 图标的版本，按 GPL-3.0 条款分发。

## AI 协助说明
本项目部分内容由生成式 AI 辅助生成，所有内容已由作者本人整理、验证与修改。

## 联系作者
- 作者：Renzic-Stone
- 邮箱：rzs_@outlook.com
