# FlpInfoer
([If you need an English README... Click here](https://github.com/Renzic-Stone/PyFlp-FlpInfoer/blob/main/README_en.md))

这是一个基于Python3.10和[PyFlp](https://github.com/demberto/PyFLP)V2.2.1的用于读取生成于[FlStudio](https://www.image-line.com/fl-studio/)的特殊格式工程文件.flp文件的第三方项目
### 目前已经实现的功能有:
1.导出所有音符(按Pattern分组)✅

2.按Pattern分文件导出音符✅

3.导出速度(BPM) ✅
### 未来将会支持:
1.按Pattern分别导出.mid文件❌

2.按音轨导出Pattem❌

3.按音轨导出完整乐曲的.mid文件❌
### 格式与位置:
导出音符格式: [开始小节:步:嘀嗒-结束小节:步:嘀嗒,音高,乐器名] (持续=ticks)

音符位置说明: 小节(1开始):步(00-15,十六进制):嘀嗒(00-23,24进制),(与FlStudio钢琴卷帘内部标记一致)

本项目致力于解决FlStudio的完整.mid文件导出功能残缺问题(无法带乐器分乐轨,批量分pattern输出)

注意❗本项目与[FlStudio](https://www.image-line.com/fl-studio/)和[FlpInfo](https://github.com/demberto/FLPInfo)无关(后者同样依靠PyFlp库,但已停止更新),所有代码均为原创/AI生成后人工修改或重写


## 本项目遵循GPL-3.0 license

本项目源码使用 GPL-3.0 license 授权，允许自由使用、修改与分发
**但打包后的发行版（即发行版中附带图标的 .exe 可执行文件）所使用图标为 Renzic_Stone 原创设计且受版权保护.禁止在未经作者授权的情况下用于商业活动（例如以任何形式在电商平台销售或在博客平台设为仅VIP可见/收费下载,但可免费上传网盘/博客分发）**

### AI 协助说明(About AI)

本项目部分由 生成式AI 辅助生成（如chatGPT等），所有内容已由作者本人整理、验证与修改。

本项目代码版权归作者所有，允许在 GPL-3.0 license 下使用。

### 图标版权声明
本项目所使用的图标（以下简称“图标”）由 Renzic_Stone 原创设计，享有完整的版权及相关知识产权。

您可以在非商业用途下自由使用、修改、分发该图标，需保留作者署名。商业用途请联系作者获取授权。

作者保留对该图标的全部版权与最终解释权。
除非另有明确说明，本图标不适用于GPL-3.0或其他开源软件许可证。

#### 若需使用本图标，请通过以下方式联系作者以获得授权：
GIthub账号:Renzic-Stone
邮箱:rzs_@outlook.com



## 联系作者
如果遇到任何问题,欢迎通过GitHub/邮件联系作者
- 作者：Renzic-Stone
- 联系方式：rzs_@outlook.com

..............
