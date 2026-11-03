"""Phigros 资源提取 —— 命令行入口（不依赖 tkinter，可在无图形界面 / 批处理下运行）。

用法示例：
    python cli.py                       # 用同目录或上级目录的 base.apk，按 config.ini 全量提取
    python cli.py D:\\1\\base.apk        # 指定安装包
    python cli.py --only chart music    # 只提取谱面和音乐（覆盖 config.ini 的开关）
    python cli.py --info-only           # 只生成 info/ 下的信息表
    python cli.py --skip-info           # 复用已有的 info/，跳过信息表生成
    python cli.py --list                # 列出安装包里的资源条目数，不写文件
"""
import argparse
import os
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
# fsb5 会在当前目录找 libvorbis.dll / libogg.dll，config.ini 和 info/ 也都是相对路径
os.chdir(HERE)
sys.path.insert(0, HERE)

import gameInformation
import resource
from log import init_console_logger

# config.ini [TYPES] 里的键 -> resource.run() 使用的配置键
TYPE_KEYS = {
    "avatar": "avatar",
    "Chart": "chart",
    "IllustrationBlur": "illustrationBlur",
    "IllustrationLowRes": "illustrationLowRes",
    "Illustration": "illustration",
    "music": "music",
}
DIRS = ("avatar", "chart", "illustrationBlur", "illustrationLowRes", "illustration", "music")
INFO_FILES = ("tmp.tsv", "difficulty.tsv", "info.tsv")


def read_config():
    from configparser import ConfigParser

    c = ConfigParser()
    c.optionxform = str
    if not c.read("config.ini", "utf8"):
        sys.exit("找不到 config.ini（应在 %s 下运行）" % HERE)
    types = c["TYPES"]
    config = {v: types.getboolean(k) for k, v in TYPE_KEYS.items()}
    config["UPDATE"] = {
        "main_story": c["UPDATE"].getint("main_story"),
        "side_story": c["UPDATE"].getint("side_story"),
        "other_song": c["UPDATE"].getint("other_song"),
    }
    return config


def find_apk(given):
    if given:
        path = os.path.abspath(given)
        if not os.path.isfile(path):
            sys.exit("安装包不存在：%s" % path)
        return path
    for candidate in (
        os.path.join(HERE, "base.apk"),
        os.path.join(os.path.dirname(HERE), "base.apk"),
    ):
        if os.path.isfile(candidate):
            return candidate
    sys.exit("未找到 base.apk，请把安装包放到 %s 或上级目录，或用参数指定路径。" % HERE)


def count_entries(apk_path):
    with zipfile.ZipFile(apk_path) as apk:
        names = apk.namelist()
    bundles = [n for n in names if n.startswith("assets/aa/Android/") and n.endswith(".bundle")]
    return names, bundles


def make_dirs(config):
    for name, on in config.items():
        if name == "UPDATE" or not on:
            continue
        if not os.path.isdir(name):
            os.mkdir(name)


def main():
    parser = argparse.ArgumentParser(description="Phigros 资源提取（命令行）")
    parser.add_argument("apk", nargs="?", help="base.apk 路径，省略时自动查找")
    parser.add_argument("--only", nargs="+", metavar="TYPE",
                        help="只提取这些类型：avatar chart illustrationBlur illustrationLowRes illustration music")
    parser.add_argument("--info-only", action="store_true", help="只生成 info/ 信息表，不提取资源")
    parser.add_argument("--skip-info", action="store_true", help="跳过 info/ 信息表生成")
    parser.add_argument("--list", action="store_true", help="只统计安装包内的资源包数量")
    args = parser.parse_args()

    logger = init_console_logger()
    apk_path = find_apk(args.apk)

    names, bundles = count_entries(apk_path)
    if "assets/aa/catalog.json" not in names:
        sys.exit("这不像 Phigros 的安装包：缺少 assets/aa/catalog.json")
    logger.info("安装包：%s（%.2f GB）", apk_path, os.path.getsize(apk_path) / 1024 ** 3)
    logger.info("资源包 %d 个，条目 %d 个", len(bundles), len(names))
    if args.list:
        return

    config = read_config()
    if args.only:
        wanted = set(args.only)
        unknown = wanted - set(DIRS)
        if unknown:
            sys.exit("未知类型：%s（可选：%s）" % (", ".join(unknown), " ".join(DIRS)))
        for name in DIRS:
            config[name] = name in wanted
    make_dirs(config)

    info_ready = all(os.path.isfile(os.path.join("info", f)) for f in INFO_FILES)
    if args.info_only or not (args.skip_info or info_ready):
        logger.info("== 读取游戏信息 -> info/ ==")
        os.makedirs("info", exist_ok=True)
        gameInformation.run(apk_path, logger)
    elif not info_ready and args.skip_info:
        sys.exit("info/ 不完整，无法复用。请去掉 --skip-info 先生成信息表。")
    if args.info_only:
        logger.info("信息表已写入 info/")
        return

    enabled = [n for n in DIRS if config.get(n)]
    if not enabled:
        sys.exit("所有资源类型都是关闭状态，请修改 config.ini 或使用 --only")
    logger.info("== 提取资源：%s ==" % ", ".join(enabled))

    # resource.save_music() 依赖模块级 FSB5，这里手动注入（原 __main__ 中的做法）
    from fsb5 import FSB5
    resource.FSB5 = FSB5
    resource.config = config
    resource.run(apk_path, logger)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("\n已中断")
