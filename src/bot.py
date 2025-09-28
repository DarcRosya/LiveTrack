# src/bot.py

import asyncio
import logging
import sys
import httpx

from aiogram import Dispatcher, F, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Import the shared bot instance from our telegram_sender service
from src.services.telegram_sender import bot
from src.config.settings import settings


# --- Configuration ---
API_URL = "http://app:8000"
HEADERS = {"X-API-Key": settings.INTERNAL_API_KEY.get_secret_value()}


# --- Finite State Machine (FSM) Definitions ---

class AuthStates(StatesGroup):
    """States for the user authentication process."""
    waiting_for_username = State()
    waiting_for_password = State()

class HabitCreationStates(StatesGroup):
    """States for the new habit creation process."""
    waiting_for_name = State()
    waiting_for_timer = State()


dp = Dispatcher()


# --- Helper Functions ---

async def make_api_request(method: str, endpoint: str, **kwargs) -> httpx.Response:
    """A centralized helper function for making API requests."""
    async with httpx.AsyncClient() as client:
        response = await client.request(method, f"{API_URL}{endpoint}", headers=HEADERS, **kwargs)
        # Will raise HTTPStatusError for 4xx/5xx responses, which we can catch
        response.raise_for_status()
        return response

async def is_user_linked(chat_id: int) -> bool:
    """Checks via the API if a chat_id is linked to any user."""
    try:
        response = await make_api_request("GET", f"/users/by-telegram/{chat_id}")
        return response.status_code == 200
    except httpx.HTTPStatusError as e:
        # A 404 error is an expected outcome, meaning the user is not linked.
        if e.response.status_code == 404:
            return False
        # For other errors (like 500), log them and assume not linked.
        logging.error(f"API error while checking if user is linked: {e}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error while checking if user is linked: {e}")
        return False


# --- Command Handlers ---

@dp.message(CommandStart())
async def handle_start(message: types.Message):
    """Greets the user and lists available commands."""
    await message.answer(
        f"👋 Hello, {message.from_user.full_name}!\n\n"
        "I'm the LiveTrack habit tracker bot. Here is what I can do:\n\n"
        "/login - Link your account from the website\n"
        "/newhabit - Create a new habit\n"
        "/cancelhabit - Cancel an existing habit"
    )

@dp.message(Command("login"))
async def handle_login(message: types.Message, state: FSMContext):
    """Starts the account linking process."""
    if await is_user_linked(message.chat.id):
        await message.answer("Your Telegram account is already linked.")
        return
    
    await state.set_state(AuthStates.waiting_for_username)
    await message.answer("Please enter your username from the LiveTrack website.")

@dp.message(Command("newhabit"))
async def handle_new_habit(message: types.Message, state: FSMContext):
    """Starts the new habit creation process if the user is linked."""
    if not await is_user_linked(message.chat.id):
        await message.answer("You must link your account first. Please use the /login command.")
        return

    await state.set_state(HabitCreationStates.waiting_for_name)
    await message.answer("Great! What should we name the new habit?")

@dp.message(Command("cancel"))
@dp.message(F.text.casefold() == "cancel")
async def handle_fsm_cancel(message: types.Message, state: FSMContext):
    """Allows a user to cancel any ongoing FSM conversation."""
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.clear()
    await message.answer("Action cancelled.")

@dp.message(Command("cancelhabit"))
async def handle_cancel_habit_list(message: types.Message):
    """Fetches and displays a list of active habits for cancellation."""
    try:
        response = await make_api_request("GET", f"/habits/bot/list/{message.chat.id}")
        habits = response.json()

        if not habits:
            await message.answer("You have no active habits to cancel.")
            return

        builder = InlineKeyboardBuilder()
        for habit in habits:
            builder.button(text=habit['name'], callback_data=f"delete_habit:{habit['id']}")
        builder.adjust(1)
        await message.answer("Which habit would you like to cancel?", reply_markup=builder.as_markup())

    except Exception as e:
        logging.error(f"Failed to get habit list for {message.chat.id}: {e}")
        await message.answer(f"❌ Failed to get your habit list. Please try again later.")

# --- Callback Query Handlers ---

@dp.callback_query(F.data.startswith("delete_habit:"))
async def handle_delete_callback(callback: types.CallbackQuery):
    """Processes the cancellation of a habit from an inline button."""
    habit_id = int(callback.data.split(":")[1])
    delete_data = {"telegram_chat_id": callback.message.chat.id}

    try:
        await make_api_request("DELETE", f"/habits/bot/delete/{habit_id}", json=delete_data)
        await callback.message.edit_text("✅ Habit successfully cancelled.")
    except Exception as e:
        logging.error(f"Failed to delete habit {habit_id} for user {callback.message.chat.id}: {e}")
        await callback.message.edit_text(f"❌ Failed to cancel the habit. Please try again.")
    
    await callback.answer()

# --- State Handlers for Authentication ---

@dp.message(AuthStates.waiting_for_username)
async def process_username(message: types.Message, state: FSMContext):
    """Receives the username and asks for the password."""
    await state.update_data(username=message.text)
    await state.set_state(AuthStates.waiting_for_password)
    await message.answer("Thank you. Now, please enter your password. The message with your password will be deleted in 10 seconds for security.")

@dp.message(AuthStates.waiting_for_password)
async def process_password(message: types.Message, state: FSMContext):
    """Receives the password and tries to link the account via the API."""
    user_data = await state.update_data(password=message.text)
    await state.clear()

    # Delete the user's message containing the password for security
    try:
        await message.delete()
    except Exception:
        pass # It's okay if this fails (e.g., not enough permissions)

    await message.answer("Checking your credentials...")
    
    link_data = {
        "username": user_data["username"],
        "password": user_data["password"],
        "telegram_chat_id": message.chat.id,
    }

    try:
        await make_api_request("POST", "/auth/bot/link", json=link_data)
        await message.answer("✅ Account linked successfully! You can now create habits with /newhabit.")
    except httpx.HTTPStatusError as e:
        detail = "Invalid username or password."
        try:
            detail = e.response.json().get("detail", detail)
        except Exception:
            pass
        await message.answer(f"❌ Linking failed: {detail}\nPlease try /login again.")
    except Exception as e:
        logging.error(f"System error during account linking: {e}")
        await message.answer(f"❌ A system error occurred. Please try again later.")

# --- State Handlers for Habit Creation ---

@dp.message(HabitCreationStates.waiting_for_name)
async def process_habit_name(message: types.Message, state: FSMContext):
    """Receives the habit name and asks for the timer."""
    await state.update_data(name=message.text)
    await state.set_state(HabitCreationStates.waiting_for_timer)
    await message.answer("Got it. Now, how often should I remind you (in seconds)?")

@dp.message(HabitCreationStates.waiting_for_timer, F.text.isdigit())
async def process_habit_timer(message: types.Message, state: FSMContext):
    """Receives the timer, creates the habit via the API, and ends the dialogue."""
    user_data = await state.update_data(timer=int(message.text))
    await state.clear()
    await message.answer("One moment, creating your habit...")

    habit_data = {
        "name": user_data["name"],
        "timer_to_notify_in_seconds": user_data["timer"],
        "telegram_chat_id": message.chat.id
    }

    try:
        await make_api_request("POST", "/habits/bot/create", json=habit_data)
        await message.answer(
            "✅ Done! Your habit has been created. The first notification will arrive shortly.\n\n"
            "You can cancel it later with the /cancelhabit command."
        )
    except httpx.HTTPStatusError as e:
        detail = "An unknown API error occurred."
        try:
            detail = e.response.json().get("detail", detail)
        except Exception:
            pass
        await message.answer(f"❌ Failed to create habit: {detail}")
    except Exception as e:
        logging.error(f"System error during habit creation: {e}")
        await message.answer(f"❌ A system error occurred. Please try again later.")

@dp.message(HabitCreationStates.waiting_for_timer)
async def process_timer_invalid(message: types.Message):
    """Handles cases where the user enters a non-digit timer value."""
    await message.answer("That doesn't look like a number. Please enter the timer in seconds, or type 'cancel'.")


# --- Bot Startup ---
async def main():
    """Initializes and starts the bot dispatcher."""
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())