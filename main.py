import secrets
import json
import asyncio
import logging
import re
import os
import sys
from scrape.bing import get_bing_images
from scrape.copilot import send_copilot_request
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
    ButtonsMessage,
    ExtendedTextMessage,
    ContextInfo
)
from neonize.types import MessageServerID
from neonize.utils import log, build_jid,get_message_type
from neonize.utils.enum import ReceiptType
import signal
import urllib.parse
import requests 

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
    from_ = message.Info.MessageSource.Chat 
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
    isGroup = message.Info.MessageSource.IsGroup
    isOwner = message.Info.MessageSource.Sender.User in ["6285124037519", "601164899724"]
    # groupMetadata = await client.get_group_info(from_) if isGroup else {}
    # participants = groupMetadata.Participants if isGroup else []
    # participant_bot = next((p for p in participants if p.JID.User == "6285124037519"), None)
    # participant_sender = next((p for p in groupMetadata.Participants if p.JID.User == message.Info.MessageSource.Sender.User),None)
    # isBotAdmin = participant_bot is not None and (participant_bot.IsAdmin or participant_bot.IsSuperAdmin)
    # isAdmin = participant_sender is not None and (participant_sender.IsAdmin or participant_sender.IsSuperAdmin)

    def Example(teks):
        return (f"*Contoh :*\n*{prefix}{command} "+ str(teks) + "*")
        
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
        case 'from':
            await client.send_message(from_,f"{from_}")
        case 'join':
            if not isOwner:
                await client.reply_message("Anda bukan owner!",message)
                return
            if not text:
                await client.reply_message("Link grupnya???",message)
                return
            await client.join_group_with_link(text)
        
        case "leave" | "outgc" | "out":
            if not isOwner:
                await client.reply_message("Anda bukan owner!",message)
                return
            if not isGroup:
                await client.reply_message('Only group!',message)
                return
            await client.leave_group(from_)
            
        case "bing":
            if not text:
                await client.reply_message(Example("arona|5 (jumlah gambar)"),message)
                return
            query = text.split("|")[0]
            count = int(text.split("|")[1])
            if count > 15:
                await client.reply_message("Max gambar hanya 15!",message)
                return
            result = get_bing_images(query,count)
            for image in result["results"]:
                url = image["original_url"]
                await client.send_image(from_,url)
                
            await client.reply_message("Sukses",message)
                
        case "groupinfo":
            info = await client.get_group_info(from_)
            await client.send_message(from_,f"{info}")

        case "meta":
            if not text:
                return await client.reply_message(Example("hai meta!"),message)
                
            await client.send_message(from_,Message(
                extendedTextMessage=ExtendedTextMessage(
                    text=text,
                    contextInfo=ContextInfo(
                        mentionedJID=["13135550002@s.whatsapp.net","6281239621820@s.whatsapp.net"]
                    )
                )
            )
            )
            
        case "copilot":
            if not text:
                return await client.reply_message(Example("bagaimana cara ngoding"),message)
                
            result = json.loads(send_copilot_request(text))
            await client.send_message(from_,result["text"])
            
            
        case "zeya":
            if not text:
                return await client.reply_message(Example("halo zeya!"),message)
                
            apiUrl = f"https://zeya.fainshe.tech/api/chat?message={urllib.parse.quote(text)}" if isGroup else f"https://zeya.fainshe.tech/api/v2/chat?message={urllib.parse.quote(text)}&sessionId={from_.User}"
            
            response = requests.get(apiUrl).json()
            await client.reply_message(response["jawaban"][0]["content"]["parts"][0]["text"],message)




@client.event(PairStatusEv)
async def PairStatusMessage(_: NewAClient, message: PairStatusEv):
    log.info(f"logged as {message.ID.User}")

# @client.blocking
# async def default_blocking(_: NewAClient):
    # log.debug("custom blocking function has been called.")
    # log.debug("🚧 The function is blocked, waiting for the event to be set.")
    # await event.wait()
    # log.debug("🚦 The function has been unblocked.")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(client.connect()) 
        
