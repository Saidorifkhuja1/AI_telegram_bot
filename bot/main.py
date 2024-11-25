import logging
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from config import BOT_TOKEN, API, API1, API2  # Import API keys and bot token from config

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Keyboards
ai_selection_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
ai_selection_keyboard.add(
    KeyboardButton("AI 1"), KeyboardButton("AI 2"), KeyboardButton("AI 3")
)

cancel_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
cancel_keyboard.add(KeyboardButton("Cancel"))

# Dictionary to store user's selected AI
user_ai_selection = {}

# Function to communicate with OpenAI API
async def get_ai_response(api_key, user_message):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": user_message}],
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logging.error(f"OpenAI API error: {response.status}, {await response.text()}")
                    return None
    except aiohttp.ClientError as e:
        logging.error(f"Network error: {e}")
        return None

# Command to start the bot
@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    await message.reply(
        f"Hello, {message.from_user.username}! Choose an AI to start chatting:",
        reply_markup=ai_selection_keyboard,
    )

# Handler for AI selection
@dp.message_handler(lambda message: message.text in ["AI 1", "AI 2", "AI 3"])
async def handle_ai_selection(message: types.Message):
    user_id = message.from_user.id
    if message.text == "AI 1":
        user_ai_selection[user_id] = API
    elif message.text == "AI 2":
        user_ai_selection[user_id] = API1
    elif message.text == "AI 3":
        user_ai_selection[user_id] = API2

    await message.reply(
        "Great! Now send me your message to start chatting or click 'Cancel' to choose another AI.",
        reply_markup=cancel_keyboard,
    )

# Handler for user messages after AI selection
@dp.message_handler(lambda message: message.from_user.id in user_ai_selection)
async def chat_with_ai(message: types.Message):
    user_id = message.from_user.id
    if message.text.lower() == "cancel":
        # Remove AI selection and show AI selection keyboard again
        user_ai_selection.pop(user_id, None)
        await message.reply(
            "AI selection canceled. Choose an AI to start chatting:",
            reply_markup=ai_selection_keyboard,
        )
        return

    api_key = user_ai_selection[user_id]
    user_message = message.text

    response = await get_ai_response(api_key, user_message)
    if response and "choices" in response:
        ai_reply = response["choices"][0]["message"]["content"]
        await message.reply(ai_reply)
    else:
        await message.reply("Sorry, I couldn't process your request. Please try again.")

# Run the bot
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
