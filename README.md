# PyFlp-FlpInfoer
这是一个基于python3.10和[PyFlp](https://github.com/demberto/PyFLP)V2.2.1的用于读取flp文件的程序,目前已经实现的功能有:
导出所有音符(按pattern分组)✅
按pattern分文件导出音符✅
导出速度: 148.0 BPM ✅
按pattern分别导出midi❌
按音轨导出pattem❌
按音轨导出完整乐曲的midi❌
导出音符格式: [开始小节:步:嘀嗒-结束小节:步:嘀嗒,音高,乐器名] (持续=ticks)
音符位置说明: 小节(1开始):步(00-15,十六进制):嘀嗒(00-23,24进制),(与FlStudio钢琴卷帘内部标记一致)
..............
本项目致力于解决FlStudio的完整.mid文件导出功能残缺问题(无法带乐器分乐轨,批量分pattern输出)
注意❗本项目与[FlpInfo](https://github.com/demberto/FLPInfo)无关,所有代码均为原创/AI生成后人工修改,优化
..............
## 本项目遵循Apache License 2.0 
AI 协助说明

本项目部分代码由 AI 辅助生成（如 GPT、DeepSeek、腾讯元宝等），所有内容已由作者本人整理、验证与修改。

本项目代码版权归作者所有，允许在 Apache License 2.0 下非商业使用。

## 商业授权声明（Commercial Use Policy）

本项目使用 Apache License 2.0 授权，允许自由使用、修改与分发，**仅限于非商业用途**。

若您希望将本项目或其修改版本用于任何商业目的（包括但不限于作为产品的一部分、提供付费服务、公司内部使用等），请联系作者获取商业授权：

- 作者：Renzic-Stone
- 联系方式：rzs_@outlook.com

未经商业授权的商用行为将被视为侵权，保留追究法律责任的权利。

..............
