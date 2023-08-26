import sqlite3
import telebot
from loguru import logger
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


    def handle_message(self, message):
        """Bot Main message handler"""
        logger.info(f"Incoming message: {message}")
        self.send_text(f"Your original message: {message.text}")

class QuoteBot(Bot):
    def handle_message(self, message):
        logger.info(f"Incoming message: {message}")


class SustainabilityBot(Bot):
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

        if message.text.startswith('/feedback'):
            self.send_feedback_button(message)

    def send_feedback_button(self, message):
        markup = telebot.types.InlineKeyboardMarkup()
        button = telebot.types.InlineKeyboardButton(
            text="Provide Feedback", callback_data="feedback"
        )
        markup.add(button)
        self.bot.send_message(
            message.chat.id,
            "Thank you for using the bot! Please provide your feedback:",
            reply_markup=markup,
        )


if __name__ == "_main_":
    _token = "6333049326:AAGZH5kjbQwKMSWWNldjkspmE18Eg6s8tTw"
    openai.api_key = "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"
    my_bot = SustainabilityBot(_token)

    conn = sqlite3.connect('feedback.db')

    conn = sqlite3.connect('feedback.db')
    cursor = conn.cursor()


    @my_bot.bot.callback_query_handler(func=lambda call: call.data == 'feedback')
    def ask_for_feedback(call):
        my_bot.bot.send_message(call.message.chat.id, "Please share your thoughts:")
        my_bot.bot.register_next_step_handler_by_chat_id(call.message.chat.id, save_feedback)


    def save_feedback(message):
        user_id = message.from_user.id
        feedback_text = message.text

        try:
            cursor.execute("INSERT INTO feedback (user_id, feedback_text) VALUES (?, ?)", (user_id, feedback_text))
            conn.commit()

            my_bot.bot.send_message(message.chat.id, "Thank you for your feedback!")

        except sqlite3.Error as e:
            my_bot.bot.send_message(message.chat.id,
                                    "An error occurred while saving your feedback Please try again later.")

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
            "/search - Write a query to search \n"
            "/motivation - If you want me to motivate you to come and study here time to time...\n"
            "/feedback - Feel free to give feedback\n"
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
    # Close the SQLite connection when the bot stops polling
    cursor.close()
    conn.close()

