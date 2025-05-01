#(©)Codexbotz

import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot import Bot
from pyrogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove
from asyncio import TimeoutError
from helper_func import encode, get_message_id, admin

@Bot.on_message(filters.private & admin & filters.command('batch'))
async def batch(client: Client, message: Message):
    while True:
        try:
            first_message = await client.ask(text = "Forward the First Message from DB Channel (with Quotes)..\n\nor Send the DB Channel Post Link", chat_id = message.from_user.id, filters=(filters.forwarded | (filters.text & ~filters.forwarded)), timeout=60)
        except TimeoutError:
            return
        f_msg_id = await get_message_id(client, first_message)
        if f_msg_id:
            break
        else:
            await first_message.reply("❌ Error\n\nthis Forwarded Post is not from my DB Channel or this Link is taken from DB Channel", quote = True)
            continue

    while True:
        try:
            second_message = await client.ask(text = "Forward the Last Message from DB Channel (with Quotes)..\nor Send the DB Channel Post link", chat_id = message.from_user.id, filters=(filters.forwarded | (filters.text & ~filters.forwarded)), timeout=60)
        except TimeoutError:
            return
        s_msg_id = await get_message_id(client, second_message)
        if s_msg_id:
            break
        else:
            await second_message.reply("❌ Error\n\nthis Forwarded Post is not from my DB Channel or this Link is taken from DB Channel", quote = True)
            continue

    # Verify that messages have any content
    invalid_messages = []
    try:
        for msg_id in range(f_msg_id, s_msg_id + 1):
            db_message = await client.get_messages(client.db_channel.id, msg_id)
            if db_message:
                has_content = bool(db_message.video or db_message.document or db_message.text or db_message.sticker or db_message.caption)
                if not has_content:
                    invalid_messages.append(msg_id)
                else:
                    caption = db_message.caption.html if db_message.caption else db_message.text.html if db_message.text else ""
                    print(f"Verified message ID {msg_id}: HasVideo={bool(db_message.video)}, HasDocument={bool(db_message.document)}, HasText={bool(db_message.text)}, HasSticker={bool(db_message.sticker)}, Caption/Text={caption}, ReplyTo={db_message.reply_to_message_id}")
            else:
                invalid_messages.append(msg_id)
                print(f"Message ID {msg_id} not found in DB channel")
            await asyncio.sleep(0.1)  # Small delay to avoid rate limits
    except Exception as e:
        await message.reply(f"⚠️ Warning: Could not verify messages:\n<code>{e}</code>", quote=True)

    if invalid_messages:
        await message.reply(f"⚠️ Warning: Messages with IDs {', '.join(map(str, invalid_messages))} have no content (video, document, text, sticker). They will be skipped.", quote=True)

    string = f"get-{f_msg_id * abs(client.db_channel.id)}-{s_msg_id * abs(client.db_channel.id)}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.username}?start={base64_string}"
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]])
    await second_message.reply_text(f"<b>Here is your link</b>\n\n{link}", quote=True, reply_markup=reply_markup)


@Bot.on_message(filters.private & admin & filters.command('genlink'))
async def link_generator(client: Client, message: Message):
    while True:
        try:
            channel_message = await client.ask(text = "Forward Message from the DB Channel (with Quotes)..\nor Send the DB Channel Post link", chat_id = message.from_user.id, filters=(filters.forwarded | (filters.text & ~filters.forwarded)), timeout=60)
        except TimeoutError:
            return
        msg_id = await get_message_id(client, channel_message)
        if msg_id:
            break
        else:
            await channel_message.reply("❌ Error\n\nthis Forwarded Post is not from my DB Channel or this Link is not taken from DB Channel", quote = True)
            continue

    # Verify that the message has content
    try:
        db_message = await client.get_messages(client.db_channel.id, msg_id)
        if db_message:
            has_content = bool(db_message.video or db_message.document or db_message.text or db_message.sticker or db_message.caption)
            if not has_content:
                await message.reply(f"⚠️ Warning: Message ID {msg_id} has no content (video, document, text, sticker). It will be skipped.", quote=True)
            else:
                caption = db_message.caption.html if db_message.caption else db_message.text.html if db_message.text else ""
                print(f"Verified message ID {msg_id}: HasVideo={bool(db_message.video)}, HasDocument={bool(db_message.document)}, HasText={bool(db_message.text)}, HasSticker={bool(db_message.sticker)}, Caption/Text={caption}, ReplyTo={db_message.reply_to_message_id}")
        else:
            await message.reply(f"⚠️ Warning: Message ID {msg_id} not found in DB channel.", quote=True)
            return
    except Exception as e:
        await message.reply(f"⚠️ Warning: Could not verify message:\n<code>{e}</code>", quote=True)

    base64_string = await encode(f"get-{msg_id * abs(client.db_channel.id)}")
    link = f"https://t.me/{client.username}?start={base64_string}"
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]])
    await channel_message.reply_text(f"<b>Here is your link</b>\n\n{link}", quote=True, reply_markup=reply_markup)


@Bot.on_message(filters.private & admin & filters.command("custom_batch"))
async def custom_batch(client: Client, message: Message):
    collected = []
    STOP_KEYBOARD = ReplyKeyboardMarkup([["STOP"]], resize_keyboard=True)

    await message.reply("Send all messages you want to include in batch.\n\nPress STOP when you're done.", reply_markup=STOP_KEYBOARD)

    while True:
        try:
            user_msg = await client.ask(
                chat_id=message.chat.id,
                text="Waiting for files/messages...\nPress STOP to finish.",
                timeout=60
            )
        except asyncio.TimeoutError:
            break

        if user_msg.text and user_msg.text.strip().upper() == "STOP":
            break

        try:
            sent = await user_msg.copy(client.db_channel.id, disable_notification=True)
            collected.append(sent.id)
        except Exception as e:
            await message.reply(f"❌ Failed to store a message:\n<code>{e}</code>")
            continue
        await asyncio.sleep(0.1)  # Small delay to avoid rate limits

    await message.reply("✅ Batch collection complete.", reply_markup=ReplyKeyboardRemove())

    if not collected:
        await message.reply("❌ No messages were added to batch.")
        return

    # Verify that messages have content
    invalid_messages = []
    try:
        for msg_id in collected:
            db_message = await client.get_messages(client.db_channel.id, msg_id)
            if db_message:
                has_content = bool(db_message.video or db_message.document or db_message.text or db_message.sticker or db_message.caption)
                if not has_content:
                    invalid_messages.append(msg_id)
                else:
                    caption = db_message.caption.html if db_message.caption else db_message.text.html if db_message.text else ""
                    print(f"Verified message ID {msg_id}: HasVideo={bool(db_message.video)}, HasDocument={bool(db_message.document)}, HasText={bool(db_message.text)}, HasSticker={bool(db_message.sticker)}, Caption/Text={caption}, ReplyTo={db_message.reply_to_message_id}")
            else:
                invalid_messages.append(msg_id)
                print(f"Message ID {msg_id} not found in DB channel")
            await asyncio.sleep(0.1)  # Small delay to avoid rate limits
    except Exception as e:
        await message.reply(f"⚠️ Warning: Could not verify messages:\n<code>{e}</code>", quote=True)

    if invalid_messages:
        await message.reply(f"⚠️ Warning: Messages with IDs {', '.join(map(str, invalid_messages))} have no content (video, document, text, sticker). They will be skipped.", quote=True)

    start_id = collected[0] * abs(client.db_channel.id)
    end_id = collected[-1] * abs(client.db_channel.id)
    string = f"get-{start_id}-{end_id}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.username}?start={base64_string}"

    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]])
    await message.reply(f"<b>Here is your custom batch link:</b>\n\n{link}", reply_markup=reply_markup)
