import zipfile
from zipfile import ZipFile
import base64
import os
import json
from io import BytesIO
from UnityPy import Environment
from queue import Queue
from concurrent.futures import ThreadPoolExecutor
import threading
from UnityPy import Environment
from UnityPy.classes import AudioClip
from UnityPy.enums import ClassIDType
from fsb5 import FSB5

class ByteReader:
    def __init__(self, data):
        self.data = data
        self.position = 0

    def readInt(self):
        self.position += 4
        return self.data[self.position - 4] ^ self.data[self.position - 3] << 8 ^ self.data[self.position - 2] << 16



if not os.path.exists("./output"):
    os.mkdir("./output")

def io():
    while True:
        item = queue_in.get()
        if item is None:
            break
        else:
            path, resource = item
            if type(resource) == BytesIO:
                with resource:
                    with open(path, "wb") as f:
                        f.write(resource.getbuffer())
            else:
                with open(path, "wb") as f:
                    f.write(resource)


def save_image(path, image):
    bytesIO = BytesIO()
    image.save(bytesIO, "png")
    queue_in.put((path, bytesIO))


def save_music(path, music: AudioClip):
    fsb = FSB5(music.m_AudioData)
    queue_in.put((path, fsb.rebuild_sample(fsb.samples[0])))

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

def save(key, entry, pool):
    global data_json
    obj = entry.get_filtered_objects(classes)
    obj = next(obj).read()
    if not key[:7] == "avatar.":
        if "Random.SobremSilentroom" in key:
            if "Random.SobremSilentroom.0" in key:
                songsName = "Random"
            elif "Random.SobremSilentroom.1" in key:
                songsName = "Random[R]"
            elif "Random.SobremSilentroom.2" in key:
                songsName = "Random[A]"
            elif "Random.SobremSilentroom.3" in key:
                songsName = "Random[N]"
            elif "Random.SobremSilentroom.4" in key:
                songsName = "Random[D]"
            elif "Random.SobremSilentroom.5" in key:
                songsName = "Random[O]"
            elif "Random.SobremSilentroom.6" in key:
                songsName = "Random[M]"
            else:
                print("error")
                exit()
        else:
            songsName = safe_file_name(data_json[key.split("/")[-2]]["fixedSongsName"])    
    else:
        return
    if "Chart_" in key:
        root = "./output/Chart/"
        filename = key.split('/')[-1]
        if filename == "Chart_EZ.json":
            root += "EZ/"
        elif filename == "Chart_HD.json":
            root += "HD/"
        elif filename == "Chart_IN.json":
            root += "IN/"
        elif filename == "Chart_AT.json":
            root += "AT/"
        elif filename == "Chart_Legacy.json":
            root += "Legacy/"
        else:
            root += "Other/"
        root += f"{songsName}/"

        if not os.path.exists(root):
            os.makedirs(root, exist_ok=True)
        queue_in.put((f"{root}/{filename}", obj.script))
    elif "IllustrationBlur.jpg" in key:
        p = "./output/IllustrationBlur/" + songsName
        if not os.path.exists(p):
            os.makedirs(p, exist_ok=True)
        bytesIO = BytesIO()
        obj.image.save(bytesIO, "png")
        queue_in.put((f"{p}/IllustrationBlur.png", bytesIO))
    elif "IllustrationLowRes.jpg" in key:
        p = "./output/IllustrationLowRes/" + songsName
        if not os.path.exists(p):
            os.makedirs(p, exist_ok=True)
        future = pool.submit(save_image, f"{p}/IllustrationLowRes.png", obj.image)
        try:
            future.result()
        except Exception as e:
            print(f"Error: {e}")
    elif "Illustration.jpg" in key:
        p = "./output/Illustration/" + songsName
        if not os.path.exists(p):
            os.makedirs(p, exist_ok=True)
        future = pool.submit(save_image, f"{p}/Illustration.png", obj.image)
        try:
            future.result()
        except Exception as e:
            print(f"Error: {e}")
    elif "music.wav" in key or "music_IN.wav" in key: #Cristalisia
        p = "./output/Music/" + songsName
        if not os.path.exists(p):
            os.makedirs(p, exist_ok=True)
        if "music_IN.wav" in key:
            future = pool.submit(save_music, f"{p}/Music_IN.ogg", obj)
        else:
            future = pool.submit(save_music, f"{p}/Music.ogg", obj)
        try:
            future.result()
        except Exception as e:
            print(f"Error: {e}")
    else:
        print(key)

def getInformation(path):
    global data_json
    GameInformation = None
    data_json = {}
    wtf = []
    with open("typetree.json") as f:
        typetree = json.load(f)
    env = Environment()


    with zipfile.ZipFile(path) as apk:
        with apk.open("assets/bin/Data/globalgamemanagers.assets") as f:
            env.load_file(BytesIO(f.read()), name="assets/bin/Data/globalgamemanagers.assets")
        with apk.open("assets/bin/Data/level0") as f:
            env.load_file(BytesIO(f.read()))

    for obj in env.objects:
        if obj.type.name != "MonoBehaviour":
            continue
        data = obj.read()
        if data.m_Script.get_obj().read().name == "GameInformation":
            GameInformation = obj.read_typetree(typetree["GameInformation"])

    
    for key, songs in GameInformation["song"].items():
        for song in songs:
            while len(song["difficulty"]) == 5 or song["difficulty"][-1] == 0.0:
                song["difficulty"].pop()
                song["charter"].pop()

            if len(song["difficulty"]) != len(song["charter"]):
                print(song["difficulty"], song["charter"])
    
            for i in range(len(song["difficulty"])):
                song["difficulty"][i] = str(round(song["difficulty"][i], 1))

            #if song["songsId"][-2:] == ".0":
                #song["songsId"] = song["songsId"][:-2]

            difficulties = {}
            if len(song["difficulty"]) >= 1:
                difficulties["EZ"] = {"charter": song["charter"][0], "difficulty": song["difficulty"][0]}
            if len(song["difficulty"]) >= 2:
                difficulties["HD"] = {"charter": song["charter"][1], "difficulty": song["difficulty"][1]}
            if len(song["difficulty"]) >= 3:
                difficulties["IN"] = {"charter": song["charter"][2], "difficulty": song["difficulty"][2]}
            if len(song["difficulty"]) >= 4:
                difficulties["AT"] = {"charter": song["charter"][3], "difficulty": song["difficulty"][3]}

            if (song["songsId"] == "AnotherMe.NeutralMoon.0"):
                song["fixedSongsName"] = "Another Me (Neutral Moon)"
            elif (song["songsId"] == "AnotherMe.DAAN.0"):
                song["fixedSongsName"] = "Another Me (DAAN)"
            else:
                song["fixedSongsName"] = song["songsName"]

            if song["fixedSongsName"] in wtf:
                print("error:",song["fixedSongsName"])
                exit()
            else:
                wtf.append(song["fixedSongsName"])

            data_json[song["songsId"]] = {
                "songsName": song["songsName"],
                "fixedSongsName": song["fixedSongsName"],
                "composer": song["composer"],
                "illustrator": song["illustrator"],
                "difficulties": difficulties
            }

    #with open("./output/data.json", "w", encoding="utf8") as f:
        #f.write(json.dumps(data_json, ensure_ascii=False, indent=4))


def run(path):
    global queue_out, queue_in, classes
    queue_out = Queue()
    queue_in = Queue()
    classes = ClassIDType.TextAsset, ClassIDType.Sprite, ClassIDType.AudioClip
    with ZipFile(path) as apk:
        with apk.open("assets/aa/catalog.json") as f:
            data = json.load(f)

    key = base64.b64decode(data["m_KeyDataString"])
    bucket = base64.b64decode(data["m_BucketDataString"])
    entry = base64.b64decode(data["m_EntryDataString"])

    table = []
    reader = ByteReader(bucket)
    for x in range(reader.readInt()):
        key_position = reader.readInt()
        key_type = key[key_position]
        key_position += 1
        if key_type == 0:
            length = key[key_position]
            key_position += 4
            key_value = key[key_position:key_position + length].decode()
        elif key_type == 1:
            length = key[key_position]
            key_position += 4
            key_value = key[key_position:key_position + length].decode("utf16")
        elif key_type == 4:
            key_value = key[key_position]
        else:
            raise BaseException(key_position, key_type)
        entry_value = None
        for i in range(reader.readInt()):
            entry_position = reader.readInt()
            entry_value = entry[4 + 28 * entry_position:4 + 28 * entry_position + 28]
            entry_value = entry_value[8] ^ entry_value[9] << 8
        table.append([key_value, entry_value])
    for i in range(len(table)):
        if table[i][1] != 65535:
            table[i][1] = table[table[i][1]][0]
    for i in range(len(table) - 1, -1, -1):
        if type(table[i][0]) == int or table[i][0][:15] == "Assets/Tracks/#" or table[i][0][:14] != "Assets/Tracks/" and \
                table[i][0][:7] != "avatar.":
            del table[i]
        elif table[i][0][:14] == "Assets/Tracks/":
            table[i][0] = table[i][0][14:]

    thread = threading.Thread(target=io)
    thread.start()
    with ThreadPoolExecutor(6) as pool:
        with ZipFile(path) as apk:
            for key, entry in table:
                env = Environment()
                env.load_file(BytesIO(apk.read("assets/aa/Android/%s" % entry)), name=key)
                for i_key, i_entry in env.files.items():
                    save(i_key, i_entry, pool)

    queue_in.put(None)
    thread.join()
getInformation("com.PigeonGames.Phigros-151.apk")
run("com.PigeonGames.Phigros-151.apk")
