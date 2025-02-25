from asyncio import run as asyncio_run
import logging
import os
from pathlib import Path

from aiohttp import ClientSession
from telethon import events
from telethon.sessions import StringSession
from telethon.sync import TelegramClient
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerChannel, InputPeerEmpty

from src.utils import *
from src.tools import load_log_files


logger = logging.getLogger(__name__)

if settings.STRING_SESSION:
    client = TelegramClient(
        StringSession(settings.STRING_SESSION),
        api_id=settings.API_ID,
        api_hash=settings.API_HASH,
    )
else:
    client = TelegramClient("bot", api_id=settings.API_ID, api_hash=settings.API_HASH)


cache = {}
anti_joy_enabled = False
anti_photo_enabled = False


async def add_member(group_id: int, user_id: int):

    dialog = await client(
        GetDialogsRequest(
            offset_date=None,
            offset_id=0,
            offset_peer=InputPeerEmpty(),
            limit=10,
            hash=0,
        )
    )

    group = next(iter([chat for chat in dialog.chats if chat.id == group_id]), None)

    target_group = InputPeerChannel(channel_id=group_id, access_hash=group.access_hash)

    user_to_add = await client.get_input_entity(user_id)

    await client(InviteToChannelRequest(target_group, [user_to_add]))


@client.on(events.ChatAction(chats=chats))
async def on_member_remove(event: events.ChatAction.Event):

    if event.user_left or event.user_kicked:
        removed_user = await event.get_user()
        chat = await event.get_chat()

        # if removed_user.id in the_boys.keys():

        #     name = the_boys.get(removed_user.id, "این")

        #     if not name.endswith("ا"):
        #         name += "و"
        #     else:
        #         name += "رو"

        # await client.send_message(chat.id, f"باز یه کصکشی {name} از گروه ریموو کرد")
        try:
            await add_member(chat.id, removed_user.id)
            logger.info("Added %s back to the group.", removed_user.first_name)
        except Exception as err:
            logger.error(
                "Failed to add %s back to the group: %s",
                removed_user.first_name,
                err,
            )
        # else:
        #     logger.info(f"{removed_user.first_name} was removed from {chat.title}.")

        # return


@client.on(events.NewMessage(chats=chats, pattern="/anti_joy"))
async def toggle_anti_joy(event: events.NewMessage.Event):
    me = await client.get_me()

    if event.sender_id != me.id:
        return

    if event.reply_to:
        replied_message = await event.get_reply_message()
        sender = await replied_message.get_sender()
        sender_id = sender.id
        if not cache.get(sender_id):
            cache[sender_id] = {}
        cache[sender_id]["anti_joy"] = not cache[sender_id].get("anti_joy", False)
        status = "enabled" if cache[sender_id]["anti_joy"] else "disabled"
        await event.respond(f"Anti joy is now {status} for {sender.first_name}.")
        logger.info(
            "Anti joy has been %s for %s by %s",
            status,
            replied_message.sender_id,
            event.sender_id,
        )
        return

    global anti_joy_enabled
    anti_joy_enabled = not anti_joy_enabled
    status = "enabled" if anti_joy_enabled else "disabled"
    await event.respond(f"Anti joy is now {status}.")
    logger.info("Anti joy has been %s by %s", status, event.sender_id)


@client.on(events.NewMessage(chats=chats, pattern="/anti_photo"))
async def toggle_anti_photo(event: events.NewMessage.Event):
    me = await client.get_me()

    if event.sender_id != me.id:
        return

    if event.reply_to:
        replied_message = await event.get_reply_message()
        sender = await replied_message.get_sender()
        sender_id = sender.id
        if not cache.get(sender_id):
            cache[sender_id] = {}
        cache[sender_id]["anti_photo"] = not cache[sender_id].get("anti_photo", False)
        status = "enabled" if cache[sender_id]["anti_photo"] else "disabled"
        await event.respond(f"Anti photo is now {status} for {sender.first_name}.")
        logger.info(
            "Anti photo has been %s for %s by %s",
            status,
            replied_message.sender_id,
            event.sender_id,
        )
        return

    global anti_photo_enabled
    anti_photo_enabled = not anti_photo_enabled
    status = "enabled" if anti_photo_enabled else "disabled"
    await event.respond(f"Anti photo is now {status}.")
    logger.info("Anti photo has been %s by %s", status, event.sender_id)


@client.on(events.NewMessage(chats=chats))
async def anti_handler(event: events.NewMessage.Event):
    if "😂" in event.text:
        if any(
            (anti_joy_enabled, cache.get(event.sender_id, {}).get("anti_joy", False))
        ):
            logger.info("Joy detected!")
            try:
                await event.message.delete()
                logger.info("Joy deleted!")
            except Exception as err:
                logger.error("Failed to delete joy: %s", err)
    if event.photo:
        if any(
            (
                anti_photo_enabled,
                cache.get(event.sender_id, {}).get("anti_photo", False),
            )
        ):
            logger.info("Photo detected!")
            try:
                await event.message.delete()
                logger.info("Photo deleted!")
            except Exception as err:
                logger.error("Failed to delete photo: %s", err)


@client.on(events.NewMessage(pattern="/ping"))
async def ping(event: events.NewMessage.Event):
    me = await client.get_me()

    if event.sender_id != me.id:
        return

    await event.reply("نه")


@client.on(events.NewMessage(pattern="/logs"))
async def send_logs(event: events.NewMessage.Event):
    me = await client.get_me()

    if event.sender_id != me.id:
        return

    files = []
    if os.path.exists("discloud.config") and os.environ.get("DISCLOUD_TOKEN"):
        app_name = read_discloud_app_name()
        app_id = await find_app_by_name(app_name, os.environ.get("DISCLOUD_TOKEN"))
        app_logs = await read_app_logs(app_id, os.environ.get("DISCLOUD_TOKEN"))
        files.append({"filename": "discloud.log", "content": app_logs})

    log_path = Path("logs")
    if log_path.exists():
        log_files = load_log_files(log_path)
        files.extend(log_files)

    if not files:
        await event.reply("No logs found.")
        return

    paste_url = await paste_files(files)
    await event.reply(paste_url, link_preview=False)


from telethon import events
import ast
import asyncio

def insert_returns(body):
    # insert return stmt if the last expression is an expression statement
    if isinstance(body[-1], ast.Expr):
        body[-1] = ast.Return(body[-1].value)
        ast.fix_missing_locations(body[-1])

    # for if statements, we insert returns into the body and the orelse
    if isinstance(body[-1], ast.If):
        insert_returns(body[-1].body)
        insert_returns(body[-1].orelse)

    # for with blocks, again we insert returns into the body
    if isinstance(body[-1], ast.With):
        insert_returns(body[-1].body)

@client.on(events.NewMessage(pattern=r'^/eval (.+)'))
async def eval_handler(event):


    me = await client.get_me()

    if event.sender_id != me.id:
        return

    try:
        code = event.pattern_match.group(1)
        fn_name = "_eval_expr"
        cmd = "\n".join(f"    {line}" for line in code.strip("` ").splitlines())
        body = f"async def {fn_name}():\n{cmd}"

        parsed = ast.parse(body)
        insert_returns(parsed.body[0].body)

        env = {
            'client': event.client,
            'event': event,
            '__import__': __import__,
            'asyncio': asyncio,
            'os': os,
        }

        exec(compile(parsed, filename="<ast>", mode="exec"), env)
        result = await eval(f"{fn_name}()", env)
    except Exception as err:
        await event.respond(f"Execution failed: {err}")

    if result is None:
        return await event.respond("✅ Code executed successfully.")
    
    result_str = str(result)
    await event.respond(result_str[:4096])  # Telegram message limit


async def main():
    await client.start()
    logger.info("Bot started.")
    me = await client.get_me()
    logger.info("Logged in as %s", me.first_name)
    await client._run_until_disconnected()


if __name__ == "__main__":
    logger.info("Starting the bot...")
    asyncio_run(main())
