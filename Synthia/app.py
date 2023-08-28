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

    def send_text_with_quote(self, text, message_id=None):
        self.send_text(text)

    def start_motivational_thread(self):
        self.motivational_thread = threading.Thread(target=self.send_motivational_message)
        self.motivational_thread.daemon = True  # Thread will exit when the main program exits
        self.motivational_thread.start()

    def stop_motivational_thread(self):
        if hasattr(self, "motivational_thread") and self.motivational_thread.is_alive():
            self.motivational_thread.join()  # Wait for the thread to finish

    def send_motivational_message(self):
        while True:
            # Your existing code to generate and send motivational messages
            for chat_id in self.user_details:
                message = self.generate_motivational_message(chat_id)
                self.send_text(message, chat_id)

            time.sleep(5)  # Sleep for 5 minutes

    def generate_motivational_message(self, chat_id):
        print("Sending motivational messages...")
        motivational_messages = [
            "Your commitment to progress is inspiring, {name}. Keep engaging with Alex and moving forward.",
            "The journey of a thousand miles begins with a single step, {name}. Keep stepping with Alex!",
            "Success is the sum of small efforts repeated daily, {name}. Keep engaging with Alex and building your success.",
            "Your determination fuels your journey, {name}. Keep returning to Alex and pursuing your goals.",
            "Believe in yourself and your ability to create positive change, {name}. Keep engaging with Alex and making a difference.",
            "Your consistent actions define your success, {name}. Keep engaging with Alex and shaping your destiny.",
            "Every interaction with Alex is a step towards realizing your potential, {name}. Keep embracing the journey.",
            "Your engagement with Alex today lays the foundation for your achievements tomorrow, {name}. Keep it up!",
            "The secret to getting ahead is getting started, {name}. Keep taking action with Alex and reaching new heights.",
            "Hi {name}, it's a new opportunity to engage with Alex and stay motivated.",
            "Hey {name}, a little progress each day adds up to big results. Keep engaging with Alex!",
            "Hello {name}, just a quick reminder that your journey to success starts with small steps. Keep going with Alex!",
            "Your dedication to self-improvement is truly inspiring, {name}. Keep up the great work with Alex!",
            "Your commitment to personal growth sets you on a path to greatness, {name}. Keep it up with Alex!",
            "Remember that every moment you spend engaging with Alex brings you closer to your goals, {name}.",
            "Your journey to success is a marathon, not a sprint, {name}. Keep engaging with Alex and progressing.",
            "A small step forward is still progress, {name}. Keep coming back to Alex and making those steps count!",
            "Every interaction with Alex contributes to your growth and success, {name}. Keep that momentum!",
            "Your efforts today shape your future, {name}. Keep engaging with Alex and reaching for your dreams.",
            "Consistency is key on the path to success, {name}. Keep returning to Alex and moving forward.",
            "Your dedication to personal development is remarkable, {name}. Keep interacting with Alex and shining!",
            "Your commitment to growth sets you apart, {name}. Keep coming back to Alex and making your mark.",
            "It's never too late to start or continue your journey, {name}. Keep engaging with Alex and thriving!",
            "Your progress matters, {name}. Keep returning to Alex and building the life you envision.",
            "Your effort today brings you closer to the person you want to become, {name}. Keep it up!",
            "Remember that every day is a new chance to make progress, {name}. Keep interacting with Alex and achieving more.",
            "You're on the right track to success, {name}. Keep coming back to Alex and staying motivated!",
            "Your journey may have ups and downs, but each step counts, {name}. Keep engaging with Alex and moving forward.",
            "Your determination is commendable, {name}. Keep returning to Alex and writing your success story!",
            "Your consistent efforts pave the way to your goals, {name}. Keep engaging with Alex and thriving.",
        ]
        return random.choice(motivational_messages).format(name=self.user_details[chat_id]['name'])

    def start(self):
        super().start()
        self.start_motivational_thread()

        self.schedule = schedule.Scheduler()  # Create the schedule instance
        # Schedule the motivational message task
        self.schedule.every(4).seconds.do(self.send_motivational_message)

        print("Scheduled tasks:")
        for job in self.schedule.get_jobs():
            print(job)

        self.bot_thread = threading.Thread(target=self.bot.infinity_polling)
        self.bot_thread.start()

    def start_bot(self):
        super().start()
        self.start_motivational_thread()
        try:
            while True:
                self.schedule.run_pending()
                time.sleep(5)  # Sleep for 2 seconds to prevent high CPU usage
        except Exception as e:
            traceback.print_exc()  # Print the exception traceback

    def stop(self):
        self.stop_motivational_thread()
        super().stop()  # Call the parent stop method to stop the bot's polling


if __name__ == "__main__":
    with open(".telegramToken2", "r") as telegram_token_file:
        _token = telegram_token_file.read().strip()

    # Load the GPT token from the file
    with open(".gptkey", "r") as gpt_token_file:
        openai_key = gpt_token_file.read().strip()
    my_bot = SustainabilityBot(_token, openai.api_key)

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
        my_bot.send_text("🌱 Welcome to Synthia, your eco-conscious companion! 🌍\n\n"
                         "I'm here to assist you in your journey towards a sustainable lifestyle. Whether you have questions about recycling, energy conservation, eco-friendly practices, or anything related to sustainability, I'm here to guide you!\n\n"
                         "Feel free to ask me questions or explore my functionalities using the commands below:\n\n"
                         "Click on /help to get started.")


    @my_bot.bot.message_handler(commands=["help"])
    def handle_help(message):
        help_text = (
            "Here are the functionalities you can use with their respective commands:\n\n"
            "/start - Get a warm welcome and introduction to Synthia\n"
            "/help - Discover the range of sustainability topics I can assist you with\n"
            "/search - Search for information on sustainable practices\n"
            "/motivation - Let me inspire you to embrace an eco-friendly lifestyle\n"
            "/feedback - Share your thoughts and help improve Synthia"
        )
        my_bot.send_text(help_text)


    @my_bot.bot.message_handler(commands=["search"])
    def handle_chatgpt(message):
        # Extract the query by removing '/chatgpt' from the start of the message text
        query = message.text.replace("/search", "").strip()
        # Call the gpt() function with the extracted query
        response = my_bot.search_gpt(query)

        my_bot.send_text_with_quote(response, message_id=message.message_id)


    @my_bot.bot.message_handler(commands=["stop"])
    def handle_stop(message):
        my_bot.send_text("Stopping the bot...")
        my_bot.stop()


    my_bot.start()

    # Close the SQLite connection when the bot stops polling
    cursor.close()
    conn.close()