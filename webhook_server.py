#!/usr/bin/env python3
"""
Веб-сервер для обработки webhook от Telegram
Использование: python3 webhook_server.py
Или с указанием хоста и порта: python3 webhook_server.py 0.0.0.0 8443
"""
import sys
import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from dotenv import load_dotenv
import os

# Импортируем основной модуль для регистрации обработчиков
import main as bot_main

load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем настройки
TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "https://yourdomain.com")  # Замените на ваш домен
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# Порт для веб-сервера (по умолчанию 8443, стандартный для Telegram webhook)
WEBAPP_HOST = os.getenv("WEBAPP_HOST", "0.0.0.0")
WEBAPP_PORT = int(os.getenv("WEBAPP_PORT", "8443"))


async def on_startup(bot: Bot) -> None:
    """Выполняется при запуске сервера"""
    # Устанавливаем webhook
    await bot.set_webhook(
        url=WEBHOOK_URL,
        drop_pending_updates=True
    )
    logger.info(f"Webhook установлен: {WEBHOOK_URL}")


async def on_shutdown(bot: Bot) -> None:
    """Выполняется при остановке сервера"""
    # Удаляем webhook
    await bot.delete_webhook()
    logger.info("Webhook удален")


def main():
    """Основная функция запуска сервера"""
    if not TOKEN:
        logger.error("BOT_TOKEN не найден в .env файле")
        sys.exit(1)
    
    # Получаем хост и порт из аргументов командной строки, если указаны
    host = sys.argv[1] if len(sys.argv) > 1 else WEBAPP_HOST
    port = int(sys.argv[2]) if len(sys.argv) > 2 else WEBAPP_PORT
    
    # Используем бота и диспетчер из основного модуля
    # Это гарантирует, что все обработчики уже зарегистрированы
    bot = bot_main.bot
    dp = bot_main.dp
    
    # Создаем приложение aiohttp
    app = web.Application()
    
    # Настраиваем обработчик webhook
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    
    # Регистрируем обработчик
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    
    # Настраиваем приложение
    setup_application(app, dp, bot=bot)
    
    # Регистрируем функции запуска и остановки
    app.on_startup.append(lambda app: on_startup(bot))
    app.on_shutdown.append(lambda app: on_shutdown(bot))
    
    # Запускаем сервер
    logger.info(f"Запуск веб-сервера на {host}:{port}")
    logger.info(f"Webhook URL: {WEBHOOK_URL}")
    logger.info("Нажмите Ctrl+C для остановки")
    
    web.run_app(app, host=host, port=port)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Сервер остановлен")

