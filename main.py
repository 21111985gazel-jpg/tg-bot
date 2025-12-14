import sys
import subprocess
import importlib
import asyncio

# ======================================================
# 1️⃣ УСТАНОВКА / ПРОВЕРКА AIOGRAM
# ======================================================
required_stable = "3.10"
package_name = "aiogram"

def install_aiogram():
    py_ver = sys.version_info
    print(f"🧩 Проверка окружения: Python {py_ver.major}.{py_ver.minor}")
    try:
        # для Python 3.13+ берём dev-ветку
        if py_ver.major == 3 and py_ver.minor > 12:
            print("⚙️ Устанавливается dev‑версия aiogram (совместимая с Python 3.13–3.14)…")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-U", "git+https://github.com/aiogram/aiogram.git@dev-3.x"])
        else:
            print(f"⚙️ Устанавливается стабильная версия aiogram {required_stable}…")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-U", f"{package_name}=={required_stable}"])
    except subprocess.CalledProcessError as e:
        print("❌ Не удалось установить aiogram:", e)
        sys.exit(1)

try:
    import aiogram
    if not aiogram.__version__.startswith("3"):
        print(f"⚠️ Установлена несовместимая версия aiogram {aiogram.__version__} → переустанавливаю…")
        install_aiogram()
        importlib.reload(aiogram)
except ImportError:
    print("📦 aiogram не найден — выполняется установка…")
    install_aiogram()

# ======================================================
# 2️⃣ ДАЛЕЕ — КОД БОТА
# ======================================================
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ⚙️ Настройки
import os

# Функция для чтения .env файла
def load_env():
    env_vars = {}
    if os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    # Убираем кавычки если есть
                    value = value.strip('"').strip("'")
                    env_vars[key.strip()] = value
    return env_vars

# Загружаем переменные из .env
env = load_env()
BOT_TOKEN = os.getenv("BOT_TOKEN") or env.get("BOT_TOKEN", "ВСТАВЬ_СВОЙ_ТОКЕН_ОТ_BOTFATHER")
MENTOR_NAME = "Гузель Фархутдинова"
MENTOR_TG = "https://t.me/guzel_farhutdinova"
CONSULT_LINK = "https://example.com/consult"
CHANNEL_LINK = "https://t.me/farhutdinova_guzel"

# Проверка токена
if BOT_TOKEN == "ВСТАВЬ_СВОЙ_ТОКЕН_ОТ_BOTFATHER":
    print("❌ ОШИБКА: Не указан токен бота!")
    print("📝 Как получить токен:")
    print("   1. Откройте Telegram и найдите @BotFather")
    print("   2. Отправьте команду /newbot")
    print("   3. Следуйте инструкциям")
    print("   4. Скопируйте полученный токен")
    print("\n💡 Затем:")
    print("   - Вставьте токен в код (строка 45), ИЛИ")
    print("   - Установите переменную окружения: $env:BOT_TOKEN='ваш_токен'")
    sys.exit(1)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
user_stage = {}

# ======================================================
# 🧱 Вспомогательная функция
# ======================================================
def make_keyboard(options):
    kb = InlineKeyboardBuilder()
    for text, cb in options:
        kb.button(text=text, callback_data=cb)
    # Каждая кнопка в отдельном ряду (width=1) - чтобы текст не обрезался
    kb.adjust(1)
    return kb.as_markup()

# ======================================================
# 💬 Логика квеста
# ======================================================

@dp.message(Command("start"))
async def start(message: types.Message):
    text = (
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        f"Я — {MENTOR_NAME}, и ты попал(а) в мини‑квест *«Твоя точка роста»*.\n\n"
        "Всего 5 коротких шагов помогут увидеть, где ты сейчас "
        "и что поможет выйти на уровень уверенности, свободы и роста 💎\n\n"
        "Готов начать?"
    )
    kb = make_keyboard([
        ("🚀 Да, стартуем", "start_game"),
        ("⏸ Не сейчас", "later")
    ])
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(lambda c: c.data == "later")
async def later(callback: types.CallbackQuery):
    await callback.message.edit_text("💫 Возвращайся, когда будешь готов(а) к росту 🌿")
    await callback.answer()

# STEP 1
@dp.callback_query(lambda c: c.data == "start_game")
async def step1(callback: types.CallbackQuery):
    user_stage[callback.from_user.id] = 1
    text = "У каждого лидера есть отправная точка.\nКакая ситуация у тебя сейчас?"
    kb = make_keyboard([
        ("🕓 Работаю много, но результата не вижу", "s1_a"),
        ("💰 Доход есть, но хочется больше свободы", "s1_b"),
        ("🚀 Хочу стартовать, но не знаю с чего начать", "s1_c")
    ])
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()

# STEP 2
@dp.callback_query(lambda c: c.data.startswith("s1_"))
async def step2(callback: types.CallbackQuery):
    user_stage[callback.from_user.id] = 2
    text = (
        "Чтобы выйти на уровень уверенности, важно понимать — что тобой движет 💡\n\n"
        "Что вдохновляет тебя сильнее всего?"
    )
    kb = make_keyboard([
        ("🧭 Развитие и рост", "s2_a"),
        ("💫 Возможности и свобода", "s2_b"),
        ("🤝 Помогать другим и быть примером", "s2_c")
    ])
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()

# STEP 3
@dp.callback_query(lambda c: c.data.startswith("s2_"))
async def step3(callback: types.CallbackQuery):
    user_stage[callback.from_user.id] = 3
    text = (
        "Большинство людей ограничивают себя мыслями «я не смогу» или «позже».\n"
        "А лидер смотрит иначе 🌍\n\n"
        "Что ты чаще выбираешь?"
    )
    kb = make_keyboard([
        ("💥 Действовать, даже если страшно", "s3_a"),
        ("⏳ Ждать идеального момента", "s3_b")
    ])
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()

# STEP 4
@dp.callback_query(lambda c: c.data in ["s3_a", "s3_b"])
async def step4(callback: types.CallbackQuery):
    user_stage[callback.from_user.id] = 4
    feedback = (
        "Вот это настрой лидера 🔥" if callback.data == "s3_a"
        else "Знаешь, идеального момента не будет. Иногда рост начинается с простого шага 💪"
    )
    text = (
        f"{feedback}\n\n"
        "Теперь представь: что бы изменилось в твоей жизни, если бы "
        "ты уже жил(а) в свободном ритме, занимаясь тем, что вдохновляет?"
    )
    kb = make_keyboard([
        ("🔥 Всё", "s4_a"),
        ("🌿 Я бы стал(а) увереннее", "s4_b"),
        ("🌍 Мог(ла) бы влиять и развиваться", "s4_c")
    ])
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()

# STEP 5
@dp.callback_query(lambda c: c.data.startswith("s4_"))
async def step5(callback: types.CallbackQuery):
    user_stage[callback.from_user.id] = 5
    text = (
        "Вот этот образ — твоя цель 💎\n\n"
        "Теперь важно понять, какие шаги и инструменты помогут тебе достичь "
        "этого состояния уверенности и свободы.\n\n"
        f"Следующий шаг — мини‑консультация с {MENTOR_NAME}, "
        "где мы разберём твою стратегию роста 🚀\n\n"
        "Выбери формат 👇"
    )
    kb = InlineKeyboardBuilder()
    kb.button(text="🗓 Записаться на консультацию", url=CONSULT_LINK)
    kb.button(text=f"💬 Написать {MENTOR_NAME}", url=MENTOR_TG)
    kb.button(text="📲 Подписаться на канал", url=CHANNEL_LINK)
    # Каждая кнопка в отдельном ряду (width=1) - чтобы текст не обрезался
    kb.adjust(1)
    await callback.message.edit_text(text, reply_markup=kb.as_markup())
    await callback.answer()

# Завершение
@dp.message(Command("thanks"))
async def thanks(message: types.Message):
    await message.answer(
        f"🔥 Отлично, {message.from_user.first_name}!\n"
        "Ты прошёл(ла) квест «Твоя точка роста» и сделал(а) первый шаг к новому уровню 💪\n"
        f"Сила — в действии! 🤍\n\n{MENTOR_NAME}"
    )

# ======================================================
# ▶️ Старт
# ======================================================
async def main():
    print("🤖 Бот запущен! Нажми Ctrl+C для остановки.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())