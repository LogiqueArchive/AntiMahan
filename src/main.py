from asyncio import run as asyncio_run

from telethon import events
from telethon.sync import TelegramClient
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerChannel, InputPeerEmpty
from utils import *



client = TelegramClient(
    'bot', 
    api_id=settings.API_ID, 
    api_hash=settings.API_HASH
)



async def add_member(group_id: int, user_id: int):

    dialog = await client(
        GetDialogsRequest(
            offset_date=None,
            offset_id=0,
            offset_peer=InputPeerEmpty(),
            limit=10,
            hash = 0
        )
    )

    group = next(
        iter([chat for chat in dialog.chats if chat.id == group_id]),
        None
    )

    target_group = InputPeerChannel(
        channel_id=group_id, 
        access_hash=group.access_hash
    )


    user_to_add = await client.get_input_entity(user_id)

    await client(InviteToChannelRequest(target_group, [user_to_add]))


@client.on(events.ChatAction(chats=chats))
async def on_member_remove(event: events.ChatAction.Event):



    if event.user_left or event.user_kicked:
        removed_user = await event.get_user()  
        chat = await event.get_chat() 

        if removed_user.id in the_boys.keys():
            
            name = the_boys.get(removed_user.id, "این")

            if not name.endswith("ا"):
                name += "و"
            else:
                name += "رو"


            await client.send_message(
                chat.id,
                f"باز یه کصکشی {name} از گروه ریموو کرد"
            )
            try:
                await add_member(chat.id, removed_user.id)
                logger.info("Added %s back to the group.", removed_user.first_name)
            except Exception as err:
                logger.error("Failed to add %s back to the group: %s", removed_user.first_name, err)
        else:
            logger.info(f"{removed_user.first_name} was removed from {chat.title}.")
    
        return

async def main():
    await client.start()
    logger.info("Bot started.")
    me = await client.get_me()
    logger.info("Logged in as %s", me.first_name)
    await client._run_until_disconnected()

if __name__ == '__main__':
    logger.info("Starting the bot...")
    asyncio_run(main())
