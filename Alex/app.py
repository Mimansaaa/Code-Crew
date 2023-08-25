import telebot
from loguru import logger
from google.cloud import speech
import os
import openai

class Bot:
    def _init_(self, token):
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
            f"{self._class.name_} is up and listening to new messages...."
        )
        logger.info(f"Telegram Bot information\n\n{self.bot.get_me()}")

        self.bot.infinity_polling()

    def send_text(self, text):
        self.bot.send_message(self.current_msg.chat.id, text)

    def send_text_with_quote(self, text, message_id):
        self.bot.send_message(
            self.current_msg.chat.id, text, reply_to_message_id=message_id
        )

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

    def handle_message(self, message):
        logger.info(f"Incoming message: {message}")



if _name_ == "_main_":
    _token = ""
    openai.api_key = ""
    my_bot = EducationBot(_token)


    @my_bot.bot.message_handler(commands=["start"])
    def handle_start(message):
        my_bot.send_text("Welcome to the SynthiaAI Bot. Click on /help to get started.")


    @my_bot.bot.message_handler(commands=["help"])
    def handle_help(message):
        help_text = (
            "How to use the bot:\n\n"
            "/start - Start the bot and get a welcome message\n"
            "/help - Get instructions on how to use the bot\n"
            "/search - Write a query to search on search\n"
            "/motivation - I'll keep motivating you time to time\n"
            "/feedback - Give feedback\n"
        )
        my_bot.send_text(help_text)


    @my_bot.bot.message_handler(commands=["search"])
    def handle_chatgpt(message):
        # Extract the query by removing '/chatgpt' from the start of the message text
        query = message.text.replace("/search", "").strip()
        # Call the gpt() function with the extracted query
        response = my_bot.search_gpt(query)

        my_bot.send_text_with_quote(response, message_id=message.message_id)


    my_bot.start()















