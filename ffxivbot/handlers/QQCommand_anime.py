from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import requests


def check_contain_chinese(check_str):
    for ch in check_str:
        if u"\u4e00" <= ch <= u"\u9fff":
            return True
    return False


def whatanime(receive, WHATANIME_API_URL):
    tmp = receive["message"]
    tmp = tmp[tmp.find("url=") : -1]
    tmp = tmp.replace("url=", "")
    img_url = tmp.replace("]", "")
    logging.debug("getting img_url:%s" % (img_url))
    logging.debug("whatanime post")
    r2 = requests.post(url=WHATANIME_API_URL, params={"url": img_url}, timeout=30)
    logging.debug("WhatAnime_res:\n%s" % (r2.text))
    if r2.status_code == 200:
        logging.debug("finished whatanime\nParsing.........")
        json_res = r2.json()
        if len(json_res["result"]) == 0:
            msg = "未找到所搜索的番剧"
        else:
            msg = ""
            for anime in json_res["result"][:2]:
                title = ""
                for item in anime["anilist"]["synonyms"]:
                    if item != "" and check_contain_chinese(item) and title == "":
                        title = item
                        break
                if anime["anilist"]["title"]["native"] != "" and title == "":
                    title = anime["anilist"]["title"]["native"]

                duration = [
                    (int(anime["from"]) // 60, int(anime["from"]) % 60),
                    (int(anime["to"]) // 60, int(anime["to"]) % 60),
                ]
                msg_t = "%s\nEP#%s\n%s:%s-%s:%s\n相似度:%.2f%%" % (
                    title,
                    anime["episode"],
                    duration[0][0],
                    duration[0][1],
                    duration[1][0],
                    duration[1][1],
                    float(anime["similarity"]) * 100,
                )
                msg += f"{msg_t}\n\n"
            msg = msg + "Powered by https://trace.moe/"
    elif r2.status_code == 413:
        msg = "图片太大啦，请压缩至10M"
    else:
        msg = "Error at whatanime API, status code %s" % (r2.status_code)
    return msg


def QQCommand_anime(*args, **kwargs):
    try:
        global_config = kwargs["global_config"]
        QQ_BASE_URL = global_config["QQ_BASE_URL"]
        WHATANIME_TOKEN = global_config["WHATANIME_TOKEN"]
        WHATANIME_API_URL = global_config["WHATANIME_API_URL"].format(WHATANIME_TOKEN)
        action_list = []
        receive = kwargs["receive"]

        logging.debug("anime_msg:%s" % (receive["message"]))
        qq = int(receive["user_id"])
        msg = ""
        if "CQ" in receive["message"] and "url=" in receive["message"]:
            msg = whatanime(receive, WHATANIME_API_URL)
        else:
            msg = "请在命令后添加图片"
        msg = msg.strip()
        if msg:
            reply_action = reply_message_action(receive, msg)
            action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)
