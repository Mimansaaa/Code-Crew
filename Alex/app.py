import telebot
from loguru import logger
import os
import openai
from google.cloud import speech

class Bot:
    def __init__(self, token):
        self.bot = telebot.TeleBot(token, threaded=False)
        self.bot.set_update_listener(self._bot_internal_handler)

        self.current_msg = None

    def _bot_internal_handler(self, messages):
        """Bot internal messages handler"""
        for message in messages:
            self.current_msg = message
            self.handle_message(message)

    def start(self):
        """Start polling msgs from users, this function never returns"""
        logger.info(
            f"{self.__class__.__name__} is up and listening to new messages...."
        )
        logger.info(f"Telegram Bot information\n\n{self.bot.get_me()}")

        self.bot.infinity_polling()

    def send_text(self, text):
        self.bot.send_message(self.current_msg.chat.id, text)

    def send_text_with_quote(self, text, message_id):
        self.bot.send_message(
            self.current_msg.chat.id, text, reply_to_message_id=message_id
        )

    def is_current_msg_photo(self):
        return self.current_msg.content_type == "photo"

    def is_current_msg_video(self):
        return self.current_msg.content_type == "video"

    def download_user_photo(self, quality=2):
        """
        Downloads the photos that sent to the Bot to `photos` directory (should be existed)
        :param quality: integer representing the file quality. Allowed values are [0, 1, 2]
        :return:
        """
        if not self.is_current_msg_photo():
            raise RuntimeError(
                f"Message content of type 'photo' expected, but got {self.current_msg.content_type}"
            )

        file_info = self.bot.get_file(self.current_msg.photo[quality].file_id)
        data = self.bot.download_file(file_info.file_path)
        folder_name = file_info.file_path.split("/")[0]

        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        with open(file_info.file_path, "wb") as photo:
            photo.write(data)

        return file_info.file_path

    def download_user_video(self, quality=2):
        if not self.is_current_msg_video():
            raise RuntimeError(
                f"Message content of type 'video' expected, but got {self.current_msg.content_type}"
            )

        file_info = self.bot.get_file(self.current_msg.video.file_id)
        data = self.bot.download_file(file_info.file_path)
        folder_name = file_info.file_path.split("/")[0]

        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        with open(file_info.file_path, "wb") as photo:
            photo.write(data)

        return file_info.file_path

    def send_image(self, image, caption, message_id):
        self.bot.send_photo(
            self.current_msg.chat.id,
            photo=image,
            caption=caption,
            reply_to_message_id=message_id,
        )

    def handle_message(self, message):
        """Bot Main message handler"""
        logger.info(f"Incoming message: {message}")
        self.send_text(f"Your original message: {message.text}")
    # ... (same as your existing Bot class)

    def handle_voice_message(self, message):
        file_id = message.voice.file_id
        file_info = self.bot.get_file(file_id)
        file_path = file_info.file_path
        voice_data = self.bot.download_file(file_path)

        # Save the voice message as an audio file
        audio_path = "voice_messages/"
        if not os.path.exists(audio_path):
            os.makedirs(audio_path)
        audio_file_path = os.path.join(audio_path, f"{file_id}.ogg")
        with open(audio_file_path, "wb") as audio_file:
            audio_file.write(voice_data)

        # Convert voice message to text using Google Speech-to-Text
        converted_text = self.convert_voice_to_text(audio_file_path)

        # Call ChatGPT to generate a response
        response = self.search_gpt(converted_text)

        # Send the response back to the user
        self.send_text_with_quote(response, message_id=message.message_id)

    def convert_voice_to_text(self, audio_file_path):
        client = speech.SpeechClient()

        with open(audio_file_path, "rb") as audio_file:
            content = audio_file.read()

        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
            sample_rate_hertz=16000,
            language_code="en-US",
        )

        response = client.recognize(config=config, audio=audio)

        if response.results:
            return response.results[0].alternatives[0].transcript
        return ""

class QuoteBot(Bot):
    def handle_message(self, message):
        logger.info(f"Incoming message: {message}")

        if message.text != "Please don't quote me":
            self.send_text_with_quote(message.text, message_id=message.message_id)



class EducationBot(Bot):
    def search_gpt(self, query):
        # Generate a response
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": query}],
            max_tokens=1024,
            n=1,
            stop=None,
            temperature=0.7,
        )

        response = completion.choices[0].message.content

        return response


if __name__ == "__main__":
    _token = "6333049326:AAGZH5kjbQwKMSWWNldjkspmE18Eg6s8tTw"
    openai.api_key = "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"
    my_bot = EducationBot(_token)

    # Add a handler for voice messages
    @my_bot.bot.message_handler(content_types=['voice'])
    def handle_voice_message(message):
        my_bot.handle_voice_message(message)


    @my_bot.bot.message_handler(commands=["start"])
    def handle_start(message):
        my_bot.send_text("Welcome to the SynthiaAI Bot. Click on /help to get started.")


    @my_bot.bot.message_handler(commands=["help"])
    def handle_help(message):
        help_text = (
            "How to use the bot:\n\n"
            "/start - Start the bot and get a welcome message\n"
            "/help - Get instructions on how to use the bot\n"
            "/chatgpt - Write a query to search on ChatGPT\n"
        )
        my_bot.send_text(help_text)


    @my_bot.bot.message_handler(commands=["chatgpt"])
    def handle_chatgpt(message):
        # Extract the query by removing '/chatgpt' from the start of the message text
        query = message.text.replace("/chatgpt", "").strip()
        # Call the gpt() function with the extracted query
        response = my_bot.search_gpt(query)

        my_bot.send_text_with_quote(response, message_id=message.message_id)


    my_bot.start()
