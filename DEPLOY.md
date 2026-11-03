# Phigros_Resource 部署说明

本目录是 Phigros（`com.PigeonGames.Phigros`）安装包 `base.apk` 的资源提取工具：
从 APK 的 Unity Addressables 资源包里导出头像、谱面、曲绘、模糊曲绘、低质量曲绘和音乐，
并读取游戏内信息生成 `info/` 下的定数、曲目、收藏品、头像、tips 等表格。

## 1. 环境

| 项 | 值 |
| --- | --- |
| Python | 3.11.9（`C:\Program Files\Python311\python.exe`） |
| 依赖 | UnityPy 1.10.18、fsb5 1.0（另需 pillow、etcpak、texture2ddecoder、brotli、lz4，均已安装） |
| 依赖位置 | 用户级 site-packages：`C:\Users\123\AppData\Roaming\Python\Python311\site-packages` |

检查依赖是否完整：

```powershell
python -c "import UnityPy, fsb5, PIL; print(UnityPy.__file__)"
```

音乐导出依赖根目录里的 `libvorbis.dll` / `libogg.dll`：`fsb5` 只会在**当前工作目录**找这两个 DLL，
所以所有入口脚本都会先 `chdir` 到本目录。请不要在别的目录直接 `python main.py`。

## 2. 目录与文件

```
Phigros_Resource-master\
├─ base.apk / D:\1\base.apk   安装包（2.30 GB，2691 个资源包）
├─ main.py                    图形界面主程序（tkinter）
├─ cli.py                     命令行入口（新增，无界面 / 批处理用）
├─ resource.py                资源包解析与导出
├─ gameInformation.py         游戏信息表 -> info/
├─ phira.py                   把导出的资源打包成 Phira 的 .pez 自制谱
├─ typetree.json              Unity 类型树（读取 MonoBehaviour 用）
├─ config.ini                 资源开关 + 版本范围（同步提取时全为 0）
├─ libvorbis.dll / libogg.dll 音频解码 DLL
├─ 提取资源.bat               双击运行命令行提取
├─ 图形界面.bat               双击打开图形界面
├─ info\                      信息表（difficulty.tsv、info.tsv、avatar.txt 等）
└─ avatar\ chart\ illustration\ illustrationBlur\ illustrationLowRes\ music\
```

## 3. 用法

### 图形界面（主程序）

双击 `图形界面.bat`，或在本目录执行：

```powershell
python main.py
```

选择安装包路径 → 勾选需要的类型 → 点“执行”。勾选状态保存在 `config.ini`。

### 命令行（推荐，可批处理 / 可看进度）

```powershell
cd D:\1\Phigros_Resource-master
python cli.py                        # 自动找同目录或上级目录的 base.apk，按 config.ini 全量提取
python cli.py D:\1\base.apk          # 指定安装包
python cli.py --only chart music     # 只提取谱面和音乐
python cli.py --info-only            # 只生成 info/
python cli.py --skip-info            # 复用已有 info/，只提取资源
python cli.py --list                 # 只统计安装包里的资源包数量
```

或直接双击 `提取资源.bat`。

### 输出

| 目录 | 内容 | 格式 |
| --- | --- | --- |
| `info/` | 定数、曲目/曲师/画师/谱师、曲绘 id、收藏品、头像、tips | TSV / TXT（UTF-8） |
| `avatar/` | 头像 | PNG 128×128 |
| `chart/` | 谱面，按曲目 id 建子目录 | `chart/<曲id>.0/EZ(HD/IN/AT).json` |
| `illustration/` | 曲绘 | PNG 2048×1080 |
| `illustrationBlur/` | 模糊曲绘 | PNG |
| `illustrationLowRes/` | 低质量曲绘 | PNG |
| `music/` | 音乐 | OGG（从 FSB5 还原，44.1 kHz） |

### 生成 Phira 自制谱

资源导出完成后（需要 `chart/`、`illustrationLowRes/`、`music/`、`info/`）：

```powershell
python phira.py
```

结果在 `phira/EZ|HD|IN|AT/<曲id>-<难度>.pez`。

## 4. 相对原仓库做的改动

1. **`main.py` 原本跑不起来**：用了 `from . import resource`（脚本方式执行会报 “attempted relative import”），
   `resource.run(path, config)` 与实际签名 `run(path, logger)` 不符，勾选框的键名 `Chart/Illustration…`
   和 `resource.run` 读取的 `chart/illustration…` 也不一致。已重写为可运行版本：绝对导入、后台线程执行、
   统一键名、结束时弹窗提示。
2. **新增 `cli.py`**：无界面入口，负责 `chdir`、建目录、注入 `fsb5`、生成/复用 `info/`，并支持按类型取舍。
3. **`resource.py` 容错**：资源包里没有 TextAsset/Sprite/AudioClip 时 `next()` 会抛 `StopIteration`，
   原先会中断整批提取；现在跳过并记一条 warning。
4. 新增 `提取资源.bat`、`图形界面.bat` 两个双击入口。
5. 清理了与提取流程无关的上游文件：`gui.py`、`untitled.py`（PyQt5 界面，需装 PyQt5 且没被任何入口引用）、
   `split.py`、`split.sh`（ffmpeg 切音频，Linux 脚本）、`taptap.py`（TapTap 接口）。需要时从
   `..\Phigros_Resource-master.zip` 里取回即可。

## 5. 已验证（2026-11-03 实际跑通）

`python cli.py D:\1\base.apk` 一次跑完，用时约 77 秒（解析 2691 个资源包），退出码 0，无 warning/error，
日志见 `run.log`。

| 输出 | 文件数 | 体积 | 说明 |
| --- | --- | --- | --- |
| `info/` | 8 | 90 KB | 327 首曲目、定数、109 个头像、320 条收藏品、tips |
| `avatar/` | 109 | 2 MB | PNG 128×128 RGBA |
| `chart/` | 1057 | 2.51 GB | 有定数的 1037 个难度谱面全部齐全，余下 20 个是额外条目（结局差分、变体 id） |
| `illustration/` | 330 | 503 MB | PNG 2048×1080 RGBA |
| `illustrationBlur/` | 330 | 18 MB | PNG |
| `illustrationLowRes/` | 330 | 77 MB | PNG |
| `music/` | 327 | 1.21 GB | OGG，`OggS` 头正常，44.1 kHz |

完整性核对：以 `info/info.tsv` + `info/difficulty.tsv` 为准，327 首曲目的谱面、音乐、曲绘**无缺失**；
唯一“无同名曲绘”的是第九章谢幕曲，它按设计输出为 `<曲id>_EZ/_HD/_IN/_AT.png` 四张差分曲绘。

抽样打开验证：`illustration/DataErr0r.Cosmograph.png`（2048×1080）、`avatar/Burn.png`（128×128）、
`chart/000AinSophAur.Yumeji.0/IN.json`（RPE formatVersion 3）、`music/BreakThroughTheBarrier.lixound.ogg`
均正常。

## 6. 备注

- `phira.py` 里写的是 `IllustrationLowRes/…`（大写 I），本工具输出目录是 `illustrationLowRes`。
  Windows 上不区分大小写，可直接跑；拷到 Linux/macOS 需要改这两处大小写。
- 音乐是 FSB5 里解出的 Vorbis，直接存成 `.ogg`，Phira / 播放器可直接读取。
- 重新提取前如果要保留旧结果，先备份对应目录：脚本对同名文件是覆盖写。
