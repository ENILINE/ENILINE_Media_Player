# 本地视频播放器

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

- 左右方向键快退/快进 5s(Ctrl 时 30s);空格播放/暂停;上下键音量,最高支持130%音量;F11 全屏
- 播放模式:播完暂停 / 列表循环 / 单集循环 / 随机播放
- 多播放列表(IDE 风格树形面板)、文件多选 / 递归目录添加、拖放添加
- 剪切/复制/粘贴/删除/重命名(不修改本地文件),Ctrl+Z 撤销 / Ctrl+Y / Ctrl+Shift+Z 重做
- 记忆播放进度

## 快速开始

```bash
pip install -r requirements.txt
python scripts/fetch_libmpv.py   # 下载 libmpv-2.dll 到 bin/
python main.py
```

## 打包成 exe

```bash
pyinstaller player.spec --noconfirm
# 产物:dist/VideoPlayer/VideoPlayer.exe
```

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
| Ctrl+Z / Ctrl+Y / Ctrl+Shift+Z | 撤销 / 重做 |
| Delete | 删除选中条目 / 列表 |
| Ctrl+X / Ctrl+C / Ctrl+V | 剪切 / 复制 / 粘贴 |
| F2 | 重命名 |

播放列表与进度数据保存在 `%APPDATA%/VideoPlayer/`.
