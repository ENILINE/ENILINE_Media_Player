# ENILINE Media Player

基于 PyQt5 + libmpv 的 Windows 本地视频/音频播放器,支持极宽变速与多播放列表.

## 功能

- 0.1–16x 倍速(步进 0.1),高倍速保持音高
- 右键(长按)临时加速,原倍速为n,则临时倍速f(n)为:
 
$$
f(n) = 
\begin{cases}
3n, & 0 < n \leq 1 \\
\dfrac{5n+4}{3}, & 1 < n \leq 4 \\
2n, & 4 < n \leq 8 \\
16, & 8 < n \leq 16
\end{cases}
$$

- 左右方向键快退/快进 5s(Ctrl 时 30s);空格播放/暂停;上下键音量(最高 130%);F11 全屏
- 播放模式:播完暂停 / 列表循环 / 单集循环 / 随机播放
- 多播放列表(IDE 风格树形面板)、文件多选 / 递归目录添加、拖放添加
- 剪切/复制/粘贴/删除/重命名(不修改本地文件),Ctrl+Z 撤销 / Ctrl+Y 重做
- 支持 22 种常见媒体格式(MP4/MKV/AVI/MOV/WMV/FLV/WebM/TS/M4V/MPG/MPEG/3GP/MP3/FLAC/WAV/OGG/OGA/AAC/M4A/WMA/Opus/MKA)
- 字幕开关 + 两种风格(黑边白字 / 白字黑底) + 拖动调整位置
- 可配置全局快捷键(播放/暂停/上一首/下一首)
- 关闭最小化到系统托盘
- 窗口大小与侧栏宽度记忆
- 播放失败自动跳过并弹窗询问

## 快速开始

```bash
pip install -r requirements.txt
python fetch_libmpv.py   # 下载 libmpv-2.dll 到 bin/
python main.py
```

## 打包

PyInstaller 打包:

```bash
pyinstaller player.spec --noconfirm
# 产物: dist/ENILINE_Media_Player/
```

Inno Setup 安装包(需安装 [Inno Setup](https://jrsoftware.org/isinfo.php)):

```bash
iscc installer.iss
# 产物: dist/ENILINE_Media_Player_Setup.exe
```

安装包支持: 程序文件安装、开始菜单快捷方式、卸载列表注册、22 种媒体格式关联(显示在 Windows"设置默认应用"中).

## 快捷键

| 按键 | 功能 |
| --- | --- |
| 空格 | 播放/暂停 |
| ← / → | 快退 / 快进 5 秒 |
| Ctrl+← / Ctrl+→ | 快退 / 快进 30 秒 |
| 长按 → | 临时加速,松开恢复 |
| ↑ / ↓ | 音量 +5 / -5 |
| F11 | 全屏 |
| F11 / Esc | 退出全屏 |
| Ctrl+Z / Ctrl+Y | 撤销 / 重做 |
| Delete | 删除选中条目 / 列表 |
| Ctrl+X / Ctrl+C / Ctrl+V | 剪切 / 复制 / 粘贴 |
| F2 | 重命名 |
| Ctrl+A | 全选当前列表内所有媒体 |

全局快捷键(设置中配置,默认禁用): 播放/暂停、上一首、下一首.

数据保存在 `%APPDATA%/ENILINE/ENILINE Media Player/`.