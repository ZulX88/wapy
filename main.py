import asyncio
import logging
import re
import os
import sys
from pathlib import Path
from datetime import timedelta
from neonize.aioze.client import NewAClient
from neonize.aioze.events import (
    ConnectedEv,
    MessageEv,
    PairStatusEv,
    ReceiptEv,
    CallOfferEv,
    event
)
from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import (
    Message,
    FutureProofMessage,
    InteractiveMessage,
    MessageContextInfo,
    DeviceListMetadata,
)
from neonize.types import MessageServerID
from neonize.utils import log, build_jid
from neonize.utils.enum import ReceiptType
import signal


sys.path.insert(0, os.getcwd())


def interrupted(*_):
    event.set()

def file_exists(file):
    return Path(file).is_file()
    
initialized_client = False

log.setLevel(logging.DEBUG)
signal.signal(signal.SIGINT, interrupted)


client = NewAClient("db.sqlite3")


@client.event(ConnectedEv)
async def on_connected(_: NewAClient, __: ConnectedEv):
    log.info("⚡ Connected")
  #  await client.send_message(build_jid(""), "Hello from Neonize!")


@client.event(ReceiptEv)
async def on_receipt(_: NewAClient, receipt: ReceiptEv):
    log.debug(receipt)


@client.event(CallOfferEv)
async def on_call(_: NewAClient, call: CallOfferEv):
    log.debug(call)


@client.event(MessageEv)
async def on_message(client: NewAClient, message: MessageEv):
    await handler(client, message)


async def handler(client: NewAClient, message: MessageEv):
    from_ = message.Info.MessageSource.Chat  # ganti nama 'from_' jadi 'from_'
    budy = (
        message.Message.conversation
        or getattr(message.Message, "extendedTextMessage", None) and message.Message.extendedTextMessage.text
        or ""
    )
    prefix_match = re.match(r"^[°•π÷×¶∆£¢€¥®™✓_=|~!?#$%^&.+\-,/\\©^]", budy)
    prefix = prefix_match.group() if prefix_match else "!"
    isCmd = budy.startswith(prefix)
    command = budy[len(prefix):].strip().split(" ")[0].lower() if isCmd else ""
    args = budy.strip().split()[1:] if isCmd else []
    text = " ".join(args)
    match command:
        case "ping":
            await client.reply_message("pong", message)
        case "_test_link_preview":
            await client.send_message(
                from_, "Test https://github.com/krypton-byte/neonize", link_preview=True
            )
        case "_sticker":
            await client.send_sticker(
                from_,
                "https://mystickermania.com/cdn/stickers/anime/spy-family-anya-smirk-512x512.png",
            )
        case "_sticker_exif":
            await client.send_sticker(
                from_,
                "https://mystickermania.com/cdn/stickers/anime/spy-family-anya-smirk-512x512.png",
                name="@Neonize",
                packname="2024",
            )
        case "_image":
            await client.send_image(
                from_,
                "https://download.samplelib.com/png/sample-boat-400x300.png",
                caption="Test",
                quoted=message,
            )
        case "_video":
            await client.send_video(
                from_,
                "https://download.samplelib.com/mp4/sample-5s.mp4",
                caption="Test",
                quoted=message,
            )
        case "_audio":
            await client.send_audio(
                from_,
                "https://download.samplelib.com/mp3/sample-12s.mp3",
                quoted=message,
            )
        case "_ptt":
            await client.send_audio(
                from_,
                "https://download.samplelib.com/mp3/sample-12s.mp3",
                ptt=True,
                quoted=message,
            )
        case "_doc":
            await client.send_document(
                from_,
                "https://download.samplelib.com/xls/sample-heavy-1.xls",
                caption="Test",
                filename="test.xls",
                quoted=message,
            )
        case "debug":
            await client.send_message(from_, message.__str__())
        case "viewonce":
            await client.send_image(
                from_,
                "https://pbs.twimg.com/media/GC3ywBMb0AAAEWO?format=jpg&name=medium",
                viewonce=True,
            )
        case "profile_pict":
            await client.send_message(from_, (await client.get_profile_picture(from_)).__str__())
        case "status_privacy":
            await client.send_message(from_, (await client.get_status_privacy()).__str__())
        case "read":
            await client.send_message(
                from_,
                (
                    await client.mark_read(
                        message.Info.ID,
                        from_=message.Info.MessageSource.Chat,
                        sender=message.Info.MessageSource.Sender,
                        receipt=ReceiptType.READ,
                    )
                ).__str__(),
            )
        case "read_channel":
            metadata = await client.get_newsletter_info_with_invite(
                "https://whatsapp.com/channel/0029Va4K0PZ5a245NkngBA2M"
            )
            err = await client.follow_newsletter(metadata.ID)
            await client.send_message(from_, "error: " + err.__str__())
            resp = await client.newsletter_mark_viewed(metadata.ID, [MessageServerID(0)])
            await client.send_message(from_, resp.__str__() + "\n" + metadata.__str__())
        case "logout":
            await client.logout()
        case "send_react_channel":
            metadata = await client.get_newsletter_info_with_invite(
                "https://whatsapp.com/channel/0029Va4K0PZ5a245NkngBA2M"
            )
            data_msg = await client.get_newsletter_messages(metadata.ID, 2, MessageServerID(0))
            await client.send_message(from_, data_msg.__str__())
            for _ in data_msg:
                await client.newsletter_send_reaction(metadata.ID, MessageServerID(0), "🗿", "")
        case "subscribe_channel_updates":
            metadata = await client.get_newsletter_info_with_invite(
                "https://whatsapp.com/channel/0029Va4K0PZ5a245NkngBA2M"
            )
            result = await client.newsletter_subscribe_live_updates(metadata.ID)
            await client.send_message(from_, result.__str__())
        case "mute_channel":
            metadata = await client.get_newsletter_info_with_invite(
                "https://whatsapp.com/channel/0029Va4K0PZ5a245NkngBA2M"
            )
            await client.send_message(
                from_,
                (await client.newsletter_toggle_mute(metadata.ID, False)).__str__(),
            )
        case "set_diseapearing":
            await client.send_message(
                from_,
                (await client.set_default_disappearing_timer(timedelta(days=7))).__str__(),
            )
        case "test_contacts":
            await client.send_message(from_, (await client.contact.get_all_contacts()).__str__())
        case "build_sticker":
            await client.send_message(
                from_,
                await client.build_sticker_message(
                    "https://mystickermania.com/cdn/stickers/anime/spy-family-anya-smirk-512x512.png",
                    message,
                    "2024",
                    "neonize",
                ),
            )
        case "build_video":
            await client.send_message(
                from_,
                await client.build_video_message(
                    "https://download.samplelib.com/mp4/sample-5s.mp4", "Test", message
                ),
            )
        case "build_image":
            await client.send_message(
                from_,
                await client.build_image_message(
                    "https://download.samplelib.com/png/sample-boat-400x300.png",
                    "Test",
                    message,
                ),
            )
        case "build_document":
            await client.send_message(
                from_,
                await client.build_document_message(
                    "https://download.samplelib.com/xls/sample-heavy-1.xls",
                    "Test",
                    "title",
                    "sample-heavy-1.xls",
                    quoted=message,
                ),
            )
        # ChatSettingsStore
        case "put_muted_until":
            await client.chat_settings.put_muted_until(from_, timedelta(seconds=5))
        case "put_pinned_enable":
            await client.chat_settings.put_pinned(from_, True)
        case "put_pinned_disable":
            await client.chat_settings.put_pinned(from_, False)
        case "put_archived_enable":
            await client.chat_settings.put_archived(from_, True)
        case "put_archived_disable":
            await client.chat_settings.put_archived(from_, False)
        case "get_chat_settings":
            await client.send_message(
                from_, (await client.chat_settings.get_chat_settings(from_)).__str__()
            )
        case "wait":
            await client.send_message(from_, "Waiting for 5 seconds...")
            await asyncio.sleep(5)
            await client.send_message(from_, "Done waiting!")
        case "shutdown":
            event.set()
        case "send_react":
            await client.send_message(
                from_,
                await client.build_reaction(
                    from_, message.Info.MessageSource.Sender, message.Info.ID, reaction="🗿"
                ),
            )
        case "edit_message":
            text = "Hello World"
            id_msg = None
            for i in range(1, len(text) + 1):
                if id_msg is None:
                    msg = await client.send_message(
                        message.Info.MessageSource.Chat, Message(conversation=text[:i])
                    )
                    id_msg = msg.ID
                await client.edit_message(
                    message.Info.MessageSource.Chat, id_msg, Message(conversation=text[:i])
                )
        case 'hi':
            await client.send_message(from_,'HALOO')

        case 'ht':
            tags=""
            group_info = await client.get_group_info(from_)
            for member in group_info:
                tags += f"@{member.JID.User}"
            await client.send_message(from_,text,False,tags.strip())



@client.event(PairStatusEv)
async def PairStatusMessage(_: NewAClient, message: PairStatusEv):
    log.info(f"logged as {message.ID.User}")

@client.blocking
async def default_blocking(_: NewAClient):
    log.debug("custom blocking function has been called.")
    log.debug("🚧 The function is blocked, waiting for the event to be set.")
    await event.wait()
    log.debug("🚦 The function has been unblocked.")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(client.connect()) 
        
