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
CONSULT_CHANNEL_ID = os.getenv("CONSULT_CHANNEL_ID") or env.get("CONSULT_CHANNEL_ID", None)
MENTOR_NAME = "Гузель Фархутдинова"
MENTOR_TG = "https://t.me/guzel_farhutdinova"
CONSULT_CHANNEL = "https://t.me/+ThJ1fpFJb-VmYzc6"  # Канал для отправки результатов
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
user_answers = {}  # Хранилище ответов пользователей

# Маппинг ответов на читаемый текст
ANSWERS_MAP = {
    "s1_a": "🕓 Работаю много, но результата не вижу",
    "s1_b": "💰 Доход есть, но хочется больше свободы",
    "s1_c": "🚀 Хочу стартовать, но не знаю с чего начать",
    "s2_a": "🧭 Развитие и рост",
    "s2_b": "💫 Возможности и свобода",
    "s2_c": "🤝 Помогать другим и быть примером",
    "s3_a": "💥 Действовать, даже если страшно",
    "s3_b": "⏳ Ждать идеального момента",
    "s4_a": "🔥 Всё",
    "s4_b": "🌿 Я бы стал(а) увереннее",
    "s4_c": "🌍 Мог(ла) бы влиять и развиваться"
}

# Функция для форматирования результатов опроса
def format_survey_results(user_id: int, user: types.User, answers: dict) -> str:
    """Форматирует результаты опроса в красивый шаблон"""
    username = user.username or "не указан"
    name = user.first_name or ""
    if user.last_name:
        name += f" {user.last_name}"
    
    result = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 *НОВАЯ ЗАЯВКА НА КОНСУЛЬТАЦИЮ*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 *Контакт:*
• Имя: {name}
• Username: @{username}
• ID: `{user_id}`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 *РЕЗУЛЬТАТЫ ОПРОСА*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1️⃣ *Текущая ситуация:*
{ANSWERS_MAP.get(answers.get('step1', ''), 'Не указано')}

2️⃣ *Что вдохновляет:*
{ANSWERS_MAP.get(answers.get('step2', ''), 'Не указано')}

3️⃣ *Подход к действиям:*
{ANSWERS_MAP.get(answers.get('step3', ''), 'Не указано')}

4️⃣ *Ожидаемые изменения:*
{ANSWERS_MAP.get(answers.get('step4', ''), 'Не указано')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💬 Связаться: @{username}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
    
    return result

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
    user_id = callback.from_user.id
    user_stage[user_id] = 1
    user_answers[user_id] = {}  # Инициализируем хранилище ответов
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
    user_id = callback.from_user.id
    user_stage[user_id] = 2
    user_answers[user_id]["step1"] = callback.data  # Сохраняем ответ
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
    user_id = callback.from_user.id
    user_stage[user_id] = 3
    user_answers[user_id]["step2"] = callback.data  # Сохраняем ответ
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
    user_id = callback.from_user.id
    user_stage[user_id] = 4
    user_answers[user_id]["step3"] = callback.data  # Сохраняем ответ
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
    user_id = callback.from_user.id
    user_stage[user_id] = 5
    user_answers[user_id]["step4"] = callback.data  # Сохраняем ответ
    text = (
        "Вот этот образ — твоя цель 💎\n\n"
        "Теперь важно понять, какие шаги и инструменты помогут тебе достичь "
        "этого состояния уверенности и свободы.\n\n"
        f"Следующий шаг — мини‑консультация с {MENTOR_NAME}, "
        "где мы разберём твою стратегию роста 🚀\n\n"
        "Выбери формат 👇"
    )
    kb = InlineKeyboardBuilder()
    kb.button(text="🗓 Записаться на консультацию", callback_data="send_to_channel")
    kb.button(text=f"💬 Написать {MENTOR_NAME}", url=MENTOR_TG)
    kb.button(text="📲 Подписаться на канал", url=CHANNEL_LINK)
    # Каждая кнопка в отдельном ряду (width=1) - чтобы текст не обрезался
    kb.adjust(1)
    await callback.message.edit_text(text, reply_markup=kb.as_markup())
    await callback.answer()

# Обработчик кнопки "Записаться на консультацию"
@dp.callback_query(lambda c: c.data == "send_to_channel")
async def send_to_channel(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    # Проверяем, что все ответы собраны
    if user_id not in user_answers or len(user_answers[user_id]) < 4:
        await callback.answer("❌ Ошибка: не все ответы собраны", show_alert=True)
        return
    
    try:
        # Форматируем результаты
        results_text = format_survey_results(
            user_id, 
            callback.from_user, 
            user_answers[user_id]
        )
        
        # Отправляем в канал
        if CONSULT_CHANNEL_ID:
            # Используем ID канала из .env
            channel_id = int(CONSULT_CHANNEL_ID)
            await bot.send_message(
                chat_id=channel_id,
                text=results_text,
                parse_mode="Markdown"
            )
        else:
            # Пробуем отправить по ссылке (может не работать для приватных каналов)
            # В этом случае нужно добавить CONSULT_CHANNEL_ID в .env
            await callback.answer(
                "❌ Ошибка: не указан ID канала. Добавьте CONSULT_CHANNEL_ID в .env",
                show_alert=True
            )
            return
        
        # Подтверждаем пользователю
        await callback.answer("✅ Ваша заявка отправлена! С вами свяжутся в ближайшее время 🚀", show_alert=True)
        
        # Обновляем сообщение
        text = (
            "✅ *Отлично! Твоя заявка отправлена* 🎉\n\n"
            f"{MENTOR_NAME} получит результаты твоего опроса и свяжется с тобой "
            "в ближайшее время для консультации 💫\n\n"
            "А пока можешь подписаться на канал и узнать больше 👇"
        )
        kb = InlineKeyboardBuilder()
        kb.button(text=f"💬 Написать {MENTOR_NAME}", url=MENTOR_TG)
        kb.button(text="📲 Подписаться на канал", url=CHANNEL_LINK)
        kb.adjust(1)
        await callback.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="Markdown")
        
    except Exception as e:
        print(f"Ошибка при отправке в канал: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже.", show_alert=True)

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