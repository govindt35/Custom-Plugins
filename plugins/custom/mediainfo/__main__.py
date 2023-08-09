"""MEDIA INFO"""

import os
import asyncio
import shlex
import re
import sys
from urllib.parse import unquote_plus
from typing import Tuple
from html_telegraph_poster import TelegraphPoster
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from userge import Message, userge

def post_to_telegraph(a_title: str, content: str) -> str:
    """Create a Telegram Post using HTML Content"""
    post_client = TelegraphPoster(use_api=True)
    auth_name = "Warish"
    post_client.create_api_token(auth_name)
    post_page = post_client.post(
        title=a_title,
        author=auth_name,
        author_url="",
        text=content,
    )
    return post_page["url"]


async def runcmd(cmd: str) -> Tuple[str, str, int, int]:
    """run command in terminal"""
    args = shlex.split(cmd)
    process = await asyncio.create_subprocess_exec(
        *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    return (
        stdout.decode("utf-8", "replace").strip(),
        stderr.decode("utf-8", "replace").strip(),
        process.returncode,
        process.pid,
    )


# Solves ValueError: No closing quotation by removing ' or " in file name
def safe_filename(path_):
    if path_ is None:
        return
    safename = path_.replace("'", "").replace('"', "")
    if safename != path_:
        os.rename(path_, safename)
    return safename


@userge.on_cmd("mi", about={
    'header': "Get Detailed Media Info by Replying or Link or File Path",
    'usage': "{tr}mi [url/File Path | reply to Media file]",
    'examples': "{tr}mi https://index.com/file.mkv"})
async def mediainfo(message: Message):
    """Get Media Info"""
    reply = message.reply_to_message
    if not reply:
        process = await message.edit("`Processing`")
        url_ = message.text.split(" ",1)[1]
        useurl_ = unquote_plus(url_)
        output_ = await runcmd(f'mediainfo "{useurl_}"')
        out = None
        if len(output_) != 0:
            out = output_[0]
        else:
            ext = url_[-3:]
            output_ = await runcmd(f'curl --silent {url_} | head --bytes 10M > temp.{ext} && mediainfo temp.{ext}')
            out = output_[0]
        body_text = f"""
    <h2>DETAILS</h2>
    <pre>{out}</pre>
    """
        link = post_to_telegraph("MediaInfo", body_text)
        if message.client.is_bot:
            markup = InlineKeyboardMarkup([[InlineKeyboardButton(text="Link", url=link)]])
            await process.edit_text("<b>MEDIA INFO</b>", reply_markup=markup)
        else:
            await message.edit(f"<b>MEDIA INFO:  [Link]({link})</b>")
    else:
        process = await message.edit("`Processing ...`")
        x_media = None
        available_media = (
            "audio",
            "document",
            "photo",
            "sticker",
            "animation",
            "video",
            "voice",
            "video_note",
            "new_chat_photo",
        )
        for kind in available_media:
            x_media = getattr(reply, kind, None)
            if x_media is not None:
                break
        if x_media is None:
            await message.err("Reply To a Vaild Media Format", del_in=3)
            return
        file_path = safe_filename(await reply.download())
        output_ = await runcmd(f'mediainfo "{file_path}"')
        out = None
        if len(output_) != 0:
            out = output_[0]
        body_text = f"""
    <h2>DETAILS</h2>
    <pre>{out or 'Not Supported'}</pre>
    """
        link = post_to_telegraph("MediaInfo", body_text)
        if message.client.is_bot:
            markup = InlineKeyboardMarkup([[InlineKeyboardButton(text=file_path, url=link)]])
            await process.edit_text("<b>MEDIA INFO</b>", reply_markup=markup)
        else:
            await message.edit(f"<b>MEDIA INFO:  [Link]({link})</b>")
        os.remove(file_path)
