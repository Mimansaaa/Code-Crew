import telebot
import random
import schedule
import threading
import time
import sqlite3
import openai
from loguru import logger
import traceback


class Bot:
    def __init__(self, token):
        self.bot = telebot.TeleBot(token, threaded=False)
        self.bot.set_update_listener(self._bot_internal_handler)

        self.current_msg = None
        self.user_details = {}

    def _bot_internal_handler(self, messages):
        """Bot internal messages handler"""
        for message in messages:
            self.current_msg = message
            self.handle_message(message)

    def start(self):
        logger.info(f"{self.__class__.__name__} is up and listening to new messages....")
        logger.info(f"Telegram Bot information\n\n{self.bot.get_me()}")

        self.bot.infinity_polling()

    def send_text(self, text, chat_id=None):
        if chat_id is None:
            chat_id = self.current_msg.chat.id
        return self.bot.send_message(chat_id, text)

    def handle_message(self, message):
        logger.info(f"Incoming message: {message}")
        self.send_text(f"Your original message: {message.text}")


class QuoteBot(Bot):
    def handle_message(self, message):
        logger.info(f"Incoming message: {message}")


class SustainabilityBot(Bot):
    def __init__(self, token, openai_key):
        super().__init__(token)
        self.openai_key = openai_key

    def search_gpt(self, query):
        response = self.generate_response(query)
        return response

    def generate_response(self, prompt):
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=150,
            api_key=self.openai_key
        )
        return response.choices[0].text.strip()

    def handle_message(self, message):
        super().handle_message(message)

        if message.text.startswith('/feedback'):
            self.send_feedback_button(message)
        elif message.text.startswith('/search'):
            self.handle_chatgpt(message)
        elif message.text.startswith('/stop'):
            self.handle_stop(message)

    def handle_chatgpt(self, message):
        user_input = message.text.replace("/search", "").strip()
        education_prompt = "You are a chatbot specialized in discussing education topics. Please provide information about educational methods, learning strategies, online courses, or any other educational subject:"
        full_prompt = education_prompt + " " + user_input
        chatbot_response = self.search_gpt(full_prompt)
        self.send_text(chatbot_response, message.chat.id)

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

    def start_motivational_thread(self):
        # Implement your motivational thread here
        pass

    def stop_motivational_thread(self):
        # Implement stopping the motivational thread here
        pass

    def start(self):
        super().start()
        self.start_motivational_thread()

        self.schedule = schedule.Scheduler()
        self.schedule.every(4).seconds.do(self.send_motivational_message)

        self.bot_thread = threading.Thread(target=self.schedule_loop)
        self.bot_thread.start()

    def schedule_loop(self):
        try:
            while True:
                self.schedule.run_pending()
                time.sleep(5)
        except Exception as e:
            traceback.print_exc()

    def stop(self):
        self.stop_motivational_thread()
        super().stop()


if __name__ == "__main__":
    with open(".telegramToken2", "r") as telegram_token_file:
        _token = telegram_token_file.read().strip()

    # Load the GPT token from the file
    with open(".gptkey", "r") as gpt_token_file:
        openai_key = gpt_token_file.read().strip()

    my_bot = SustainabilityBot(_token, openai_key)

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
            # Connect to the SQLite database and create a cursor
            conn = sqlite3.connect('feedback.db')
            cursor = conn.cursor()

            # Create the 'feedback' table if it doesn't exist
            cursor.execute('''
                            CREATE TABLE IF NOT EXISTS feedback (
                                user_id INTEGER,
                                feedback_text TEXT,
                                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                            )
                        ''')

            cursor.execute("INSERT INTO feedback (user_id, feedback_text) VALUES (?, ?)", (user_id, feedback_text))
            conn.commit()

            cursor.close()
            conn.close()

            my_bot.bot.send_message(message.chat.id, "Thank you for your feedback!")

        except sqlite3.Error as e:
            my_bot.bot.send_message(message.chat.id,
                                    "An error occurred while saving your feedback. Please try again later.")


    @my_bot.bot.message_handler(commands=["motivation"])
    def handle_motivation(message):
        chat_id = message.chat.id
        if chat_id not in my_bot.user_details:
            my_bot.user_details[chat_id] = {
                'name': None,
                'state': 'waiting_for_name'
            }
            my_bot.send_text("Hi! We'll keep motivating you to come and study with me.")
            my_bot.send_text("So, what's your name?", chat_id)
        else:
            my_bot.send_text("You're already registered for motivational messages!")


    @my_bot.bot.message_handler(
        func=lambda message: my_bot.user_details.get(message.chat.id, {}).get('state') == 'waiting_for_name')
    def receive_name(message):
        chat_id = message.chat.id
        my_bot.user_details[chat_id]['name'] = message.text
        my_bot.user_details[chat_id]['state'] = 'registered'
        my_bot.send_text("Thank you, {}. You're all set.".format(my_bot.user_details[chat_id]['name']), chat_id)
        my_bot.start_motivational_thread()  # Start the motivational thread after name is received


    @my_bot.bot.message_handler(commands=["start"])
    def handle_start(message):
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


    @my_bot.bot.message_handler(commands=["stop"])
    def handle_stop(message):
        my_bot.send_text("Stopping the bot...")
        my_bot.stop()


    my_bot.start()

    # Close the SQLite connection when the bot stops polling
    cursor.close()
    conn.close()

