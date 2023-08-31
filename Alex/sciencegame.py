from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, ConversationHandler, CallbackContext,Filters

with open(".telegramToken", "r") as telegram_token_file:
    _token = telegram_token_file.read().strip()

DIFFICULTY, QUESTION = range(2)

questions = {
    "easy": [
        ("What is the process by which plants make their own food?", "photosynthesis"),
        ("Which planet is known as the 'Red Planet'?", "mars"),
        ("What gas do plants use for photosynthesis?", "carbon dioxide"),
        ("What is the chemical symbol for water?", "h2o"),
        ("How many bones are there in the adult human body?", "206")
    ],
    "medium": [
        ("What is the chemical symbol for gold?", "au"),
        ("What is the smallest unit of an element?", "atom"),
        ("Which gas do plants release during photosynthesis?", "oxygen"),
        ("Who is known as the father of modern physics?", "einstein"),
        ("What is the chemical symbol for oxygen?", "o2")
    ],
    "hard": [
        ("What is the largest organ in the human body?", "skin"),
        ("Which gas is responsible for the color of the Earth's sky?", "nitrogen"),
        ("What is the process of a liquid turning into a gas at the surface?", "evaporation"),
        ("What is the chemical symbol for lead?", "pb"),
        ("What is the molecular formula for glucose?", "c6h12o6")
    ]
}

def game_start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Welcome to the Science Guess Game! Choose a difficulty level: easy, medium, or hard.")
    return DIFFICULTY

def select_difficulty(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text.strip().lower()
    if user_input in ["easy", "medium", "hard"]:
        context.user_data["difficulty"] = user_input
        context.user_data["score"] = 0
        context.user_data["question_number"] = 0
        update.message.reply_text(f"You've selected {user_input} level.\n")
        ask_question(update, context)
        return QUESTION
    else:
        update.message.reply_text("Invalid difficulty level. Choose easy, medium, or hard.")
        return DIFFICULTY

def ask_question(update: Update, context: CallbackContext) -> None:
    difficulty = context.user_data["difficulty"]
    question_number = context.user_data["question_number"]

    if question_number >= len(questions[difficulty]):
        total_score = context.user_data["score"]
        update.message.reply_text(f"Game Over! Your total score is: {total_score} out of {len(questions[difficulty])}.")
        context.user_data.clear()
        return

    question, _ = questions[difficulty][question_number]
    update.message.reply_text(question)

    context.user_data["current_answer"] = questions[difficulty][question_number][1]
    context.user_data["question_number"] += 1

def check_answer(update: Update, context: CallbackContext) -> None:
    user_answer = update.message.text.strip().lower()
    correct_answer = context.user_data["current_answer"]

    if user_answer == correct_answer:
        update.message.reply_text("Correct!")
        context.user_data["score"] += 1
    else:
        update.message.reply_text(f"Incorrect. The correct answer is: {correct_answer}")

    ask_question(update, context)



def game_main():
    updater = Updater(_token)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("sciencegame", game_start)],
        states={
            DIFFICULTY: [MessageHandler(Filters.text & ~Filters.command, select_difficulty)],
            QUESTION: [MessageHandler(Filters.text & ~Filters.command, check_answer)]
        },
        fallbacks=[],
    )

    dispatcher.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()

'''if __name__ == "__main__":
    main()'''
