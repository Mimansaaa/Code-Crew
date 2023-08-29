import random
import schedule
import threading
import time
import sqlite3
from loguru import logger
import traceback
import telebot
import speech_recognition as sr
from pydub import AudioSegment
import openai
from gtts import gTTS
import tempfile
import os


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
            if message.text:
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
        self.recognizer = sr.Recognizer()  # Initialize the speech recognition object

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
            "Hello {name}, it's another day to contribute to a more sustainable future. Keep up the great work!",
            "Your dedication to sustainability is inspiring, {name}. Keep making eco-friendly choices with Synthia!",
            "Every small action counts, {name}. Your efforts are helping to create a greener planet with Synthia.",
            "Your commitment to sustainability sets a positive example for others, {name}. Keep up the good work!",
            "The Earth thanks you for your efforts, {name}. Continue making a positive impact with Synthia.",
            "Your actions matter, {name}. Keep working towards a more sustainable world with Synthia's guidance.",
            "The journey to a sustainable world starts with you, {name}. Keep making conscious choices with Synthia!",
            "Your dedication to sustainability is a step towards a brighter future, {name}. Keep up the great work!",
            "Sustainability is a path of progress, {name}. Keep moving forward with Synthia and making a difference.",
            "Thank you for being an eco-warrior, {name}. Your actions are making a positive change with Synthia.",
            "Every effort you make for sustainability is a step towards a better planet, {name}. Keep it up!",
            "Your passion for sustainability shines through, {name}. Keep making the world a better place with Synthia.",
            "By choosing sustainability, you're leaving a positive mark on the world, {name}. Keep up the good work!",
            "Your dedication to a sustainable lifestyle is truly commendable, {name}. Keep it up with Synthia!",
            "Sustainability is a journey, and you're on the right path, {name}. Keep making a difference with Synthia.",
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

    # def stop(self):
    #     self.stop_motivational_thread()
    #     super().stop()  # Call the parent stop method to stop the bot's polling

    def handle_voice_message(self, message):
        try:
            # Download and save the voice message
            file_info = self.bot.get_file(message.voice.file_id)
            downloaded_file = self.bot.download_file(file_info.file_path)

            voice_path = "voice_message.ogg"
            with open(voice_path, 'wb') as new_file:
                new_file.write(downloaded_file)

            # Convert OGG to WAV format
            audio = AudioSegment.from_ogg(voice_path)
            audio.export("voice_message.wav", format="wav")

            # Recognize the speech
            with sr.AudioFile("voice_message.wav") as source:
                audio = self.recognizer.record(source)
                command = self.recognizer.recognize_google(audio)

            # Generate and send response
            response = self.generate_response(command)
            self.send_voice_response(message.chat.id, response)

            os.remove(voice_path)  # Clean up the temporary voice file

        except Exception as e:
            error_message = f"Error: {str(e)}"
            self.send_text(error_message, message.chat.id)

    def recognize_speech(self, audio_path):
        with sr.AudioFile(audio_path) as source:
            audio = self.recognizer.record(source)
            command = self.recognizer.recognize_google(audio)
        return command

    def generate_response(self, input_text):
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=f"You: {input_text}\nBot:",
            max_tokens=50
        ).choices[0].text.strip()
        return response

    def send_voice_response(self, chat_id, response):
        tts = gTTS(response)
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
            tts.save(temp_file.name)

        with open(temp_file.name, 'rb') as voice_file:
            self.bot.send_voice(chat_id, voice_file)

        os.remove(temp_file.name)

    def handle_text_message(self, message):
        try:
            input_text = message.text

            response = self.generate_response(input_text)
            self.send_voice_response(message.chat.id, response)

        except Exception as e:
            error_message = f"Error: {str(e)}"
            self.send_text(error_message, message.chat.id)


if __name__ == "__main__":
    with open(".telegramToken2", "r") as telegram_token_file:
        _token = telegram_token_file.read().strip()

    # Load the GPT token from the file
    with open(".gptKey2", "r") as gpt_token_file:
        openai.api_key = gpt_token_file.read().strip()
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
            "/feedback - Share your thoughts and help improve Synthia\n"
            "/voice - Ask Questions through voice or text"
        )
        my_bot.send_text(help_text)


    @my_bot.bot.message_handler(commands=["search"])
    def handle_chatgpt(message):
        # Extract the query by removing '/chatgpt' from the start of the message text
        query = message.text.replace("/search", "").strip()
        # Call the gpt() function with the extracted query
        response = my_bot.search_gpt(query)

        my_bot.send_text_with_quote(response, message_id=message.message_id)


    @my_bot.bot.message_handler(content_types=['voice'])
    def handle_voice(message):
        my_bot.handle_voice_message(message)


    # Register the text message handler
    @my_bot.bot.message_handler(func=lambda message: True)
    def handle_text(message):
        my_bot.handle_text_message(message)


    my_bot.start()

    # Close the SQLite connection when the bot stops polling
    cursor.close()
    conn.close()