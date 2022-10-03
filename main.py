import os
import time
import logging

from whisper_utils import start_whisper, transcribe

from dotenv import load_dotenv
from telegram import Update, Message
from telegram.constants import ChatAction
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes, Updater, CallbackContext


AUDIO_LEN_LIMIT_SEC = 30 * 60  # 30 minutes limit
AUDIO_LEN_LIMIT_MSG = "Sorry, your audio is too long! I currently can transcribe only 30min recordings 🐣"

START_MSG = "I'm a bot that does transcription of your voice messages in (almost) " + \
             "any language using OpenAI Whisper API. Try me by sending a voice message to this chat!"
NON_VOICE_ERR_MSG = "I can only transcribe the audio messages that you send here! Please don't send me " + \
                    "any other content, or I will ignore it.\n\n" + \
                    "I don't mean to be rude, I'm just a 🤖! Here is a bouquet of 🌹 for you: 🌹🌹🌹."
TRANSCRIPTION_EMPTY_MSG = "Oh, shoot! I couldn't transcribe what you said this time. Can you try again? Please-e? 👀"
MODE_SET_TRANSCRIBE_MSG = "I will now transcribe your messages in the language they are spoken! 🔣"
MODE_SET_TRANSLATE_MSG = "I will now transcribe everything in English! 💂"

BOT_STATE = dict(
    whisper_mode="transcribe"
)


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=START_MSG,
    )


async def response_non_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=NON_VOICE_ERR_MSG,
    )


async def response_voice(update: Update, context: CallbackContext):
    logging.info("Received request. Processing..")

    start_time = time.time()

    message = update.effective_message
    if message.voice.duration > AUDIO_LEN_LIMIT_SEC:
        message.reply_text(AUDIO_LEN_LIMIT_MSG, quote=True)
        return

    chat_id = update.effective_message.chat.id
    file_name = '%s_%s%s.ogg' % (chat_id, update.message.from_user.id, update.message.message_id)
    await download_and_prep(file_name, message)

    transcription = await transcribe(file_name, BOT_STATE["whisper_mode"])

    logging.info("Received transcription:" + transcription)

    if len(transcription) == 0 or transcription[0] == '':
        await message.reply_text(TRANSCRIPTION_EMPTY_MSG, quote=True)
        return

    await reply_long_message(message, transcription)

    delete_file(file_name)

    logging.info("Finished processing request. Time took: %s seconds" % (time.time() - start_time))


async def reply_long_message(message, transcription):
    msgs = [transcription[i:i + 4096] for i in range(0, len(transcription), 4096)]
    for text in msgs:
        await message.reply_text(text=text)


def delete_file(file_name):
    if os.path.exists(file_name):
        os.remove(file_name)


async def download_and_prep(file_name: str, message: Message) -> None:
    await message.reply_chat_action(action=ChatAction.TYPING)
    msg_file = await message.voice.get_file()
    await msg_file.download(file_name)


async def set_transcribe_given_language(update: Update, context: CallbackContext):
    BOT_STATE["whisper_mode"] = "transcribe"
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=MODE_SET_TRANSCRIBE_MSG,
    )


async def set_translate_to_english(update: Update, context: CallbackContext):
    BOT_STATE["whisper_mode"] = "translate"
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=MODE_SET_TRANSLATE_MSG,
    )


if __name__ == '__main__':
    # Starting Whisper
    logging.info("Starting Whisper...")

    start_whisper()

    logging.info("Started Whisper.")

    # Connecting to bot API
    logging.info("Connecting to the Telegram bot API...")

    load_dotenv()
    api_token = os.getenv('TELEGRAM_BOT_API_TOKEN')
    application = ApplicationBuilder().token(api_token).build()

    logging.info("Connected to the Telegram bot API.")

    # Setting up bot
    logging.info("Setting up Telegram bot...")

    start_handler = CommandHandler('start', start)
    transcribe_handler = CommandHandler('set_transcribe_given_language', set_transcribe_given_language)
    translate_handler = CommandHandler('set_translate_to_english', set_translate_to_english)
    non_voice_handler = MessageHandler(~filters.VOICE & (~filters.COMMAND), response_non_voice)
    voice_handler = MessageHandler(filters.VOICE, response_voice)

    application.add_handler(start_handler)
    application.add_handler(transcribe_handler)
    application.add_handler(translate_handler)
    application.add_handler(non_voice_handler)
    application.add_handler(voice_handler)

    logging.info("Set up Telegram bot.")

    # Running bot
    application.run_polling()
