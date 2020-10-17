from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random
import dice
import feedparser
import traceback
import requests
import time
import math
import difflib
import urllib.parse
from bs4 import BeautifulSoup


def QQCommand_hso(*args, **kwargs):
    try:
        QQ_BASE_URL = kwargs["global_config"]["QQ_BASE_URL"]
        action_list = []
        receive = kwargs["receive"]
        bot = kwargs["bot"]
        user = QQUser.objects.get(user_id=receive["user_id"])
        if time.time() < user.last_api_time + 15:
            msg = "[CQ:at,qq={}] 技能冷却中".format(user)
        else:
            msg = "好色哦"
            second_command_msg = receive["message"].replace("/hso", "", 1).strip()
            if second_command_msg.startswith("enable") or second_command_msg.startswith(
                "disable"
            ):
                if int(bot.owner_id) != int(receive["user_id"]):
                    msg = "您不是 {} 的领养者，无法修改该功能".format(bot)
                else:
                    bot.r18 = second_command_msg.startswith("enable")
                    bot.save(update_fields=["r18"])
                    msg = "真的好色哦" if bot.r18 else "不能再色了"
            elif not bot.r18:
                msg = "好色哦"
            elif second_command_msg.startswith("add"):
                second_command_msg = second_command_msg.replace("add", "", 1).strip()
                segs = second_command_msg.split(" ")
                if len(segs) >= 2:
                    (alter, _) = HsoAlterName.objects.get_or_create(name=segs[0])
                    alter.key = segs[1]
                    alter.save()
                    msg = 'hso替换命令追加:"{}"->"{}"'.format(segs[0], segs[1])
                else:
                    msg = '请输入"/hso add $name1 $name2"将$name1替换成$name2'
            else:
                page = random.randint(1, 50)
                params = "limit=20&page={}".format(page)
                if second_command_msg != "":
                    alter_tags = HsoAlterName.objects.all()
                    for alter in alter_tags:
                        second_command_msg = second_command_msg.replace(
                            alter.name, alter.key
                        )
                    tag_name = second_command_msg.replace(" ", "_")
                    tag_name = urllib.parse.quote(tag_name)
                    tag_url = "https://konachan.com/tag.json?name={}".format(tag_name)
                    r = requests.get(tag_url, timeout=(5, 60))
                    tags = r.json()
                    if tags:
                        tag_name_list = list(map(lambda x: x["name"], tags))
                        close_matches = difflib.get_close_matches(
                            tag_name, tag_name_list
                        )
                        # print("close_matches:{}".format(", ".join(close_matches)))
                        tag_name = close_matches[0]
                        count = 0
                        for tag in tags:
                            if tag["name"] == tag_name:
                                count = tag["count"]
                        params = (
                            ""
                            if count <= 100
                            else "page={}&".format(
                                random.randint(1, math.ceil(count / 100))
                            )
                        )
                        params += "tags={}".format(tag_name)
                api_url = "https://konachan.com/post.json?{}".format(params)
                # print(api_url + "\n===============================================")
                r = requests.get(api_url, timeout=(5, 60))
                img_json = r.json()

                if receive["message_type"] == "group":
                    tmp_list = []
                    for item in img_json:
                        if item["rating"] == "s":
                            tmp_list.append(item)
                    img_json = tmp_list

                if not img_json:
                    msg = "未能找到所需图片"
                else:
                    img = random.choice(img_json)
                    msg = "[CQ:image,file={}]".format(img["sample_url"])
                    user.last_api_time = time.time()
                    user.save(update_fields=["last_api_time"])

        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)
        traceback.print_exc()
    return []
