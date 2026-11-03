import os
import csv
import shutil
import zipfile
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "output"


def move_into_output(src: Path):
    dest = OUTPUT / src.name
    shutil.move(str(src), str(dest))

OUTPUT.mkdir(exist_ok=True)
info_tsv = ROOT / "info" / "info.tsv"
move_into_output(info_tsv)

for name in ("music", "illustration", "chart"):
    folder = ROOT / name
    for item in sorted(folder.iterdir()):
        move_into_output(item)

for name in ("info", "music", "illustration", "chart"):
    shutil.rmtree(ROOT / name)

os.chdir("output")

def safe_file_name(name):
    name = name.rstrip()
    replacements = {
        "\\": "＼",
        "/": "／",
        ":": "：",
        "*": "＊",
        "?": "？",
        '"': "＂",
        "<": "＜",
        ">": "＞",
        "|": "｜",
    }
    for a, b in replacements.items():
        name = name.replace(a, b)
    if name.endswith("."):
        name += "‌"
    return name


for i in os.listdir("."):
    if os.path.isdir(i):
        if not i.endswith(".0"):
            print("不支持的铺面文件夹:", i)
            shutil.rmtree(i)


with open("info.tsv", "r", encoding="utf-8") as f:
    reader = csv.reader(f, delimiter="\t")
    for i in reader:
        if len(i) >= 2:
            chart = i[0] + ".0";
            music = i[0] + ".ogg";
            illustration = i[0] + ".png"

            if not os.path.exists(chart):
                raise Exception("铺面文件夹不存在: " + chart)

            for a in ["AT", "IN", "HD", "EZ"]:
                if os.path.exists(os.path.join(chart, f"{a}.json")):
                    shutil.move(os.path.join(chart, f"{a}.json"), os.path.join(chart, f"Chart_{a}.json"))

            if not os.path.exists(music):
                raise Exception("音乐文件夹不存在: " + music)
            shutil.move(music, os.path.join(chart, "Music.ogg"))

            if not os.path.exists(illustration):
                count = 0;
                for a in ["AT", "IN", "HD", "EZ"]:
                    if os.path.exists(i[0] + f"_{a}.png"):
                        shutil.move(i[0] + f"_{a}.png", os.path.join(chart, f"Illustration_{a}.png"))
                        count += 1
                if count == 0:
                    raise Exception("曲绘文件夹不存在: " + illustration)
            else:
                shutil.move(illustration, os.path.join(chart, "Illustration.png"))


            if i[0] == "AnotherMe.NeutralMoon":
                shutil.move(chart, "Another Me (Neutral Moon)")
            elif i[0] == "AnotherMe.DAAN":
                shutil.move(chart, "Another Me (DAAN)")
            else:
                shutil.move(chart, safe_file_name(i[1]))


base_dir = Path(".")

for folder in base_dir.iterdir():
    if not folder.is_dir():
        continue

    with zipfile.ZipFile(base_dir / f"{folder.name}.zip", "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(folder):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(folder)
                zf.write(file_path, arcname)

    print(f"已压缩: {folder.name}")
    shutil.rmtree(folder)
