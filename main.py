"""Phigros 资源提取 —— 图形界面主程序。

运行：python main.py
勾选需要的资源类型后点“执行”，结果输出到本目录下的 avatar/ chart/ illustration/
illustrationBlur/ illustrationLowRes/ music/ 以及 info/。
"""
import atexit
import os
import sys
import threading
import tkinter
from tkinter import filedialog, messagebox
from configparser import ConfigParser

HERE = os.path.dirname(os.path.abspath(__file__))
# config.ini、info/ 以及 libvorbis.dll 都按当前目录定位
os.chdir(HERE)
sys.path.insert(0, HERE)

import gameInformation
import resource
from log import init_console_logger

TYPES = ("avatar", "Chart", "IllustrationBlur", "IllustrationLowRes", "Illustration", "music")
LABELS = {
    "avatar": "头像",
    "Chart": "谱面",
    "IllustrationBlur": "曲绘(模糊)",
    "IllustrationLowRes": "曲绘(低质量)",
    "Illustration": "曲绘",
    "music": "音乐",
}
DIRS = {
    "avatar": "avatar",
    "Chart": "chart",
    "IllustrationBlur": "illustrationBlur",
    "IllustrationLowRes": "illustrationLowRes",
    "Illustration": "illustration",
    "music": "music",
}

logger = init_console_logger()


def find_apk():
    for candidate in (os.path.join(HERE, "base.apk"), os.path.join(os.path.dirname(HERE), "base.apk")):
        if os.path.isfile(candidate):
            return candidate
    return ""


c = ConfigParser()
c.optionxform = str
c.read("config.ini", "utf8")

root = tkinter.Tk()
root.title("Phigros 资源提取")

row = tkinter.Frame(root)
row.pack(fill="x", padx=8, pady=6)
tkinter.Label(row, text="安装包").pack(side="left")
path_var = tkinter.StringVar(value=find_apk())
tkinter.Entry(row, textvariable=path_var, width=52).pack(side="left", padx=6)


def browse():
    chosen = filedialog.askopenfilename(title="选择 Phigros 安装包", filetypes=[("APK", "*.apk"), ("所有文件", "*.*")])
    if chosen:
        path_var.set(chosen)


tkinter.Button(row, text="浏览…", command=browse).pack(side="left")

d = {key: tkinter.BooleanVar(value=c["TYPES"].getboolean(key) if c.has_option("TYPES", key) else False)
     for key in TYPES}
for key in TYPES:
    tkinter.Checkbutton(root, text=LABELS[key], variable=d[key], anchor="w").pack(fill="x", padx=16)


def exit_handle():
    for key in TYPES:
        c["TYPES"][key] = str(d[key].get())
    with open("config.ini", "w", encoding="utf8") as f:
        c.write(f)


atexit.register(exit_handle)

run_button = tkinter.Button(root, text="执行", height=2)
run_button.pack(fill="x", padx=8, pady=8)


def extract(apk_path, config):
    if not os.path.isfile(apk_path):
        messagebox.showerror("路径错误", "安装包不存在：\n%s" % apk_path)
        return
    for name, on in DIRS.items():
        if config[on] and not os.path.isdir(DIRS[name]):
            os.mkdir(DIRS[name])
    os.makedirs("info", exist_ok=True)

    run_button.config(state="disabled")
    try:
        logger.info("== 读取游戏信息 -> info/ ==")
        gameInformation.run(apk_path, logger)
        logger.info("== 提取资源 ==")
        from fsb5 import FSB5
        resource.FSB5 = FSB5
        resource.config = config
        resource.run(apk_path, logger)
    except Exception as e:
        logger.exception("提取失败")
        root.after(0, lambda: messagebox.showerror("提取失败", "%s: %s" % (type(e).__name__, e)))
    else:
        root.after(0, lambda: messagebox.showinfo("完成", "资源已提取到：\n%s" % HERE))
    finally:
        root.after(0, lambda: run_button.config(state="normal"))


def callback():
    config = {
        "avatar": d["avatar"].get(),
        "chart": d["Chart"].get(),
        "illustrationBlur": d["IllustrationBlur"].get(),
        "illustrationLowRes": d["IllustrationLowRes"].get(),
        "illustration": d["Illustration"].get(),
        "music": d["music"].get(),
        "UPDATE": {
            "main_story": c["UPDATE"].getint("main_story"),
            "side_story": c["UPDATE"].getint("side_story"),
            "other_song": c["UPDATE"].getint("other_song"),
        },
    }
    if not any(config[k] for k in ("avatar", "chart", "illustrationBlur", "illustrationLowRes", "illustration", "music")):
        messagebox.showwarning("未选择", "请至少勾选一种资源类型")
        return
    threading.Thread(target=extract, args=(path_var.get().strip(), config), daemon=True).start()


run_button.config(command=callback)
root.mainloop()
