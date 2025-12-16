#!/usr/bin/env python3
"""
Скрипт для принудительного запуска бота локально
Останавливает все процессы и ждет, пока серверный экземпляр не освободит соединение
"""
import asyncio
import subprocess
import sys
import time
from dotenv import load_dotenv
import os
from aiogram import Bot

load_dotenv()

async def force_cleanup():
    """Принудительная очистка webhook и ожидание"""
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("❌ BOT_TOKEN не найден в .env файле")
        return False
    
    bot = Bot(token=token)
    
    try:
        print("🔄 Очистка webhook...")
        # Многократная очистка
        for i in range(5):
            try:
                await bot.delete_webhook(drop_pending_updates=True)
                print(f"✅ Webhook очищен (попытка {i+1}/5)")
            except Exception as e:
                print(f"⚠️ Попытка {i+1}: {e}")
            await asyncio.sleep(2)
        
        print("\n⏳ Ожидание 60 секунд, чтобы серверный экземпляр освободил соединение...")
        print("   (Если конфликт продолжается, нужно остановить бота на сервере)")
        
        for i in range(60, 0, -10):
            print(f"   Осталось ~{i} секунд...")
            await asyncio.sleep(10)
        
        print("\n✅ Ожидание завершено. Теперь можно запускать бота.")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False
    finally:
        await bot.session.close()

if __name__ == "__main__":
    print("🛑 Остановка всех процессов бота...")
    subprocess.run(["pkill", "-9", "-f", "main.py"], 
                   stdout=subprocess.DEVNULL, 
                   stderr=subprocess.DEVNULL)
    time.sleep(2)
    
    print("🧹 Принудительная очистка...\n")
    asyncio.run(force_cleanup())
    
    print("\n🚀 Теперь запустите бота командой: python3 main.py")


