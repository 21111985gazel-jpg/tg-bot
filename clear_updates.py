#!/usr/bin/env python3
"""Скрипт для очистки webhook и ожидающих обновлений"""
from dotenv import load_dotenv
import os
import asyncio
from aiogram import Bot

load_dotenv()
bot = Bot(token=os.getenv('BOT_TOKEN'))

async def reset():
    try:
        # Удаляем webhook
        await bot.delete_webhook(drop_pending_updates=True)
        print("✅ Webhook удален и обновления сброшены")
        
        # Получаем обновления с timeout=0, чтобы очистить очередь
        try:
            updates = await bot.get_updates(offset=-1, timeout=0)
            print(f"✅ Получено обновлений: {len(updates)}")
        except Exception as e:
            print(f"⚠️ Ошибка при получении обновлений: {e}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(reset())

