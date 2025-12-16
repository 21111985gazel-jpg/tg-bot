#!/usr/bin/env python3
"""
Скрипт для установки webhook для Telegram бота
Использование: python3 set_webhook.py <webhook_url>
Пример: python3 set_webhook.py https://yourdomain.com/webhook
"""
import sys
import asyncio
from dotenv import load_dotenv
import os
from aiogram import Bot

load_dotenv()

async def set_webhook(webhook_url: str):
    """Устанавливает webhook для бота"""
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("❌ Ошибка: BOT_TOKEN не найден в .env файле")
        return False
    
    bot = Bot(token=token)
    
    try:
        # Устанавливаем webhook
        result = await bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=True
        )
        
        if result:
            print(f"✅ Webhook успешно установлен: {webhook_url}")
            
            # Проверяем информацию о webhook
            webhook_info = await bot.get_webhook_info()
            print(f"📊 Информация о webhook:")
            print(f"   URL: {webhook_info.url}")
            print(f"   Ожидающих обновлений: {webhook_info.pending_update_count}")
            print(f"   Последняя ошибка: {webhook_info.last_error_message or 'Нет'}")
            return True
        else:
            print("❌ Не удалось установить webhook")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при установке webhook: {e}")
        return False
    finally:
        await bot.session.close()

async def delete_webhook():
    """Удаляет webhook"""
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("❌ Ошибка: BOT_TOKEN не найден в .env файле")
        return False
    
    bot = Bot(token=token)
    
    try:
        result = await bot.delete_webhook(drop_pending_updates=True)
        if result:
            print("✅ Webhook успешно удален")
            return True
        else:
            print("❌ Не удалось удалить webhook")
            return False
    except Exception as e:
        print(f"❌ Ошибка при удалении webhook: {e}")
        return False
    finally:
        await bot.session.close()

async def get_webhook_info():
    """Получает информацию о текущем webhook"""
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("❌ Ошибка: BOT_TOKEN не найден в .env файле")
        return
    
    bot = Bot(token=token)
    
    try:
        webhook_info = await bot.get_webhook_info()
        print(f"📊 Информация о webhook:")
        print(f"   URL: {webhook_info.url or 'Не установлен'}")
        print(f"   Ожидающих обновлений: {webhook_info.pending_update_count}")
        print(f"   Последняя ошибка: {webhook_info.last_error_message or 'Нет'}")
        print(f"   Последняя ошибка (дата): {webhook_info.last_error_date or 'Нет'}")
    except Exception as e:
        print(f"❌ Ошибка при получении информации: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python3 set_webhook.py <webhook_url>  - установить webhook")
        print("  python3 set_webhook.py delete         - удалить webhook")
        print("  python3 set_webhook.py info            - информация о webhook")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "delete":
        asyncio.run(delete_webhook())
    elif command == "info":
        asyncio.run(get_webhook_info())
    else:
        webhook_url = sys.argv[1]
        if not webhook_url.startswith("https://"):
            print("❌ Ошибка: Webhook URL должен начинаться с https://")
            sys.exit(1)
        asyncio.run(set_webhook(webhook_url))


