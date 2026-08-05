全部 14 项问题已完成并验证,exe 已重建。

## 完成情况

| # | 问题 | 处理 |
|---|---|---|
| 1 | `.gitignore` + README | 已添加(.gitignore 忽略 build/dist/libmpv/pycache;README 含快速开始、打包、快捷键) |
| 2/3 | 界面老旧、文字按钮 | 深色现代 QSS 主题 + 自绘 SVG 图标(播放/暂停/上下个/静音/全屏),模式按钮保留文字 |
| 4 | 倍速/音量点击轨道偏移 | 新增 `JumpSlider`:点击直接跳到鼠标位置(且取消长按 page-step 漂移) |
| 5 | 进度条点击无效 | 同 JumpSlider,点击即定位并 seek(实测中点击跳到 127s/254s) |
| 6 | 音量按钮崩溃 | 根因是 python-mpv 1.0.8 读 `mute` 属性在特定状态硬崩溃;改为 `command('set','mute')` + Python 侧维护状态 |
| 7 | 倍速/音量不精确 | 倍速:`[-] [spin 0.1–16x] [+]`(长按连调、可直接输入 0.8);音量:滑条 + 当前值显示 |
| 8 | 空格被按钮抢焦点 | 空格无条件切换播放/暂停(按钮不再窃取焦点) |
| 9 | 最小宽度过大 | 视频区 320x180→160x90,树形面板最小宽度归零 |
| 10 | 底部按钮意义不明 | 删除,全部移入右键菜单 |
| 11 | 缺键盘快捷键 | 树内支持 Delete/Ctrl+X/C/V/F2;Ctrl+Z/Y/Shift+Z 全局撤销重做 |
| 12 | 双栏合并 | 改为 IDE 风格树形列表(列表=文件夹、条目=文件),位于视频区**左侧** |
| 13 | 布局挤 | 控制栏独立成底部整条两行(进度行 + 控制行),新增「上一个/下一个」 |
| 14 | 弹窗改名 | 列表/条目重命名与新建均改为**原位内联编辑**(Esc 取消) |

## 验证
- 19 项 QTest 断言全部通过(静音不崩溃、倍速 0.8 精确、进度/音量点击跳转、Ctrl+X/C/V/Delete、内联重命名与新建、上一/下一、空格焦点、方向键按焦点区分)
- 定位并修复了 2 个自引入的崩溃:树刷新信号重入、树在自身 keyPressEvent 内 clear(改为下一事件循环延迟刷新)
- exe 重建成功(QtSvg 已打包),启动、优雅关闭、配置持久化均正常

产物仍为 [dist/VideoPlayer/VideoPlayer.exe](dist/VideoPlayer/VideoPlayer.exe);源码运行 `python main.py`。


- 原先,文件栏有添加目录/文件功能,这个功能似乎只能在此处进入,但随着双栏合并,似乎没有办法再添加文件了.
  - 一方面请恢复这个功能(比如可以右击列表弹出添加);
  - 另一方面,请添加功能:
    - 加入两个列表:临时列表和默认列表,其中前者不可删除,且每次关闭(或者等效地,启动)程序时清空其中.后者和普通列表无区别.
    - 允许直接将文件/文件夹拖到exe上,或者说允许将支持的文件用这个exe打开.打开后加入临时列表并开始播放.注意鲁棒性,预防类型不符的文件,或者空目录/不含支持类型文件的目录
    - 允许将文件夹/文件拖动至列表实现添加,允许将文件/文件夹拖动至其它位置以加入临时列表.
- 如果当前没有播放视频,拖到进度条会使程序崩溃,报错:

```
Traceback (most recent call last):
  File "C:\Users\wbz\Desktop\b\player_app\ui\main_window.py", line 231, in _on_controls_seek
    self.player.seek(t, relative=False)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^
  File "C:\Users\wbz\Desktop\b\player_app\core\mpv_player.py", line 84, in seek
    self._player.command("seek", str(seconds), "absolute")
    ~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\wbz\AppData\Local\Programs\Python\Python314\Lib\site-packages\mpv.py", line 1257, in command
    _mpv_command_node(self.handle, ppointer, out)
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\wbz\AppData\Local\Programs\Python\Python314\Lib\site-packages\mpv.py", line 162, in raise_for_ec
    raise ex
SystemError: ('Error running mpv command', -12, (<MpvHandle object at 0x0000019D981C9F90>, <ctypes.LP_MpvNode object at 0x0000019D98181EB0>, <ctypes.LP_MpvNode object at 0x0000019D98181C70>))
```

你可以考虑灵活处理,比如直接禁止在没视频时拖进度条.

- 字体改成`Consolas`,字号调大并相应地更改UI
- 倍速控制器中,左右已经有`-` `+`按钮了,但在输入框右侧仍然有用于上下调节倍速的箭头图案的小型按钮.虽能正常使用但显得多余.能否删除这两个小按钮?
- 静音图标没有正常显示(如果我没理解错的话,那个按钮应该就是用来静音的吧?),并且静音并不会使右侧的音量调归零,音量数字也正常显示非0数.
- 目录树栏和右侧的视频播放栏间的分界线,如果向右拖动是正常的,但向左拖动会导致在右侧遗留分界线和原目录树栏的残影.必须通过改变窗口大小的方式才能清除.
- 原位重命名的功能固然基本实现,但其命名窗口被一个小窗限制了.这个窗口的大小只有一条项目高度的一半高,并且默认的左右宽度只比原先的名字的宽度多一点.比如,如果原来的列表名只有一个`a`,那么这个宽度几乎只有两个`a`左右,再往里头敲字符的时候会向左溢出.能否删掉这个小窗口?如果你不能理解我指的是什么,请指出.

因为我无法找到添加并播放视频的方法,无法做进一步测试,请先修复以上问题.