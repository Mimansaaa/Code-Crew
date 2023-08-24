import os
from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext
import openai

# Set your OpenAI API key here
openai.api_key = ""
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Send me an audio message to transcribe.")

def transcribe_audio(update: Update, context: CallbackContext):
    if update.message.audio:
        audio = update.message.audio

        # Download the audio file to the local system
        audio_file = audio.get_file()
        audio_path = audio.file_id + ".mp3"
        audio_file.download(audio_path)

        print("Downloaded audio file:", audio_path)

        # Transcribe using OpenAI API
        transcription = openai.Audio.translate("whisper-1", "audio.mp3")
        transcribed_text = transcription['text']
        print("Transcription:", transcribed_text)

        if transcribed_text:
            update.message.reply_text("Transcription: " + transcribed_text)
        else:
            update.message.reply_text("Transcription failed.")

        # Clean up - delete downloaded audio file
        os.remove(audio_path)
    else:
        update.message.reply_text("Please send an audio message.")

def main():
    # Set your Telegram bot token here
    telegram_token = ""

    updater = Updater(token=telegram_token, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, start))
    dispatcher.add_handler(MessageHandler(Filters.audio, transcribe_audio))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
