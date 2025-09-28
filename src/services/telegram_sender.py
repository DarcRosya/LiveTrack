import logging
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from src.config.settings import settings

# Create a single, shared Bot instance that can be imported elsewhere.
bot = Bot(token=settings.telegram.BOT_TOKEN.get_secret_value())

async def send_message(chat_id: int, text: str) -> bool:
    """
    Sends a text message to a specified Telegram user.

    :param chat_id: The user's Telegram Chat ID.
    :param text: The message text to send.
    :return: True if the message was sent successfully, False otherwise.
    """
    try:
        await bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
        logging.info(f"Successfully sent message to chat_id: {chat_id}")
        return True
    except TelegramAPIError as e:
        # It's better to catch specific library exceptions.
        logging.error(f"Failed to send message to chat_id {chat_id}: {e}")
        return False
    except Exception as e:
        # A general fallback for other unexpected errors.
        logging.error(f"An unexpected error occurred while sending a message to {chat_id}: {e}")
        return False