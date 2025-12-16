# main.py — aiogram 3.x с двумя ветками (Здоровье/Доход)
import os
import asyncio
import requests
import logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# --------------------------------------------------------------------------
# ЗАГРУЗКА НАСТРОЕК
# --------------------------------------------------------------------------
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
AMO_API_URL = os.getenv("AMO_API_URL")
AMO_ACCESS_TOKEN = os.getenv("AMO_ACCESS_TOKEN")
CHANNEL_URL = os.getenv("CHANNEL_URL") or "https://t.me/farhutdinova_guzel"  # Fallback на дефолтный канал
CHANNEL_ID = -1003317524713  # ID канала для проверки подписки

# Проверка наличия CHANNEL_URL
if CHANNEL_URL:
    logging.info(f"CHANNEL_URL: {CHANNEL_URL}")
else:
    logging.error(f"CHANNEL_URL не установлен! Текущее значение: {repr(CHANNEL_URL)}")
REF_LINK_WOMAN = os.getenv("REF_LINK_WOMAN")
REF_LINK_MAN = os.getenv("REF_LINK_MAN")
CONSULTANT_LINK = os.getenv("CONSULTANT_LINK")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# --------------------------------------------------------------------------
# СОСТОЯНИЯ FSM
# --------------------------------------------------------------------------
class HealthForm(StatesGroup):
    name = State()
    age = State()
    height = State()
    weight = State()
    gender = State()

class IncomeForm(StatesGroup):
    welcome = State()
    name = State()
    age = State()
    desired_income = State()
    work_format = State()
    work_style = State()
    experience = State()
    sphere = State()
    skills = State()
    time_invest = State()
    values = State()
    ready_start = State()
    need_start = State()
    gender = State()

# --------------------------------------------------------------------------
# ХРАНИЛИЩЕ
# --------------------------------------------------------------------------
user_data = {}

def clamp_points(points: int) -> int:
    return 20 if points > 20 else points

# --------------------------------------------------------------------------
# Функция фейерверка брильянтов
# --------------------------------------------------------------------------
async def diamond_fireworks(message_or_callback):
    """Показывает один брильянт после исчезновения мотивационного текста"""
    await asyncio.sleep(0.3)
    if hasattr(message_or_callback, 'answer'):
        await message_or_callback.answer("💎")
    else:
        await message_or_callback.message.answer("💎")
    await asyncio.sleep(0.3)

# --------------------------------------------------------------------------
# Функция показа брильянта с задержкой
# --------------------------------------------------------------------------
async def show_diamond_with_delay(message_or_callback, balance: int):
    """Показывает брильянт с небольшой задержкой для эффекта"""
    await asyncio.sleep(0.7)  # Задержка перед показом брильянта
    
    # Показываем большой брильянт эмодзи 💎
    if hasattr(message_or_callback, 'answer'):
        await message_or_callback.answer("\n\n\n          💎\n\n\n")
    else:
        await message_or_callback.message.answer("\n\n\n          💎\n\n\n")
    
    await asyncio.sleep(1)
    
    # Показываем баланс
    if hasattr(message_or_callback, 'answer'):
        await message_or_callback.answer(f"💎 +1 брильянт! Баланс: {balance} 💎")
    else:
        await message_or_callback.message.answer(f"💎 +1 брильянт! Баланс: {balance} 💎")

# --------------------------------------------------------------------------
# Проверка подписки на канал
# --------------------------------------------------------------------------
async def check_subscription(user_id: int) -> bool:
    try:
        logging.info(f"check_subscription: проверка для пользователя {user_id}, канал ID: {CHANNEL_ID}")
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        logging.info(f"check_subscription: статус пользователя {user_id} = {member.status}")
        # Проверяем статус: member, administrator, creator
        is_member = member.status in ["member", "administrator", "creator"]
        logging.info(f"check_subscription: результат для {user_id} = {is_member}")
        return is_member
    except Exception as e:
        error_msg = str(e)
        logging.error(f"check_subscription: ОШИБКА при проверке подписки для {user_id}: {error_msg}", exc_info=True)
        
        # Если канал не найден или бот не имеет доступа - разрешаем продолжить
        # (возможно, канал недоступен или бот не добавлен в канал)
        if "chat not found" in error_msg.lower() or "not found" in error_msg.lower():
            logging.warning(f"check_subscription: Канал не найден или недоступен. Разрешаем продолжить для {user_id}")
            return True  # Разрешаем продолжить, если канал недоступен
        
        # При других ошибках возвращаем False
        return False

# --------------------------------------------------------------------------
# Отправка в AMOCRM
# --------------------------------------------------------------------------
def send_to_amocrm(user_id: int):
    data = user_data.get(user_id, {})
    payload = {
        "name": data.get("name", str(user_id)),
        "custom_fields_values": [
            {"field_name": "Telegram ID", "values": [{"value": user_id}]},
            {"field_name": "Имя", "values": [{"value": data.get('name')}]},
            {"field_name": "Ветка", "values": [{"value": data.get('branch')}]},
            {"field_name": "Пол", "values": [{"value": data.get('gender')}]},
            {"field_name": "Бриллианты", "values": [{"value": data.get('diamonds', 0)}]},
        ],
    }
    headers = {"Authorization": f"Bearer {AMO_ACCESS_TOKEN}", "Content-Type": "application/json"}
    try:
        requests.post(AMO_API_URL, json=payload, headers=headers, timeout=10)
    except Exception as e:
        print(f"AMOCRM send error: {e}")

# --------------------------------------------------------------------------
# СТАРТ — главное меню
# --------------------------------------------------------------------------
@dp.message(Command("start"))
async def start(message: Message):
    user_id = message.from_user.id
    logging.info(f"start: команда /start от пользователя {user_id}")
    
    # Проверяем реферальную ссылку
    inviter_id = None
    if message.text and len(message.text.split()) > 1:
        try:
            ref_text = message.text.split()[1]
            if ref_text.startswith("ref"):
                inviter_id = int(ref_text[3:])
                logging.info(f"start: пользователь {user_id} пришел по реферальной ссылке от {inviter_id}")
        except ValueError:
            inviter_id = None

    # Реферальная ссылка всегда ведет на основного бота @CoralClubAssistantBot
    REF_BOT_USERNAME = "CoralClubAssistantBot"
    user_data[user_id] = {
        "diamonds": 0,
        "branch": None,
        "answers": {},
        "ref_link": f"https://t.me/{REF_BOT_USERNAME}?start=ref{user_id}",
        "inviter_id": inviter_id
    }
    logging.info(f"start: данные пользователя {user_id} инициализированы")
    
    # Если пришёл по реферальной ссылке
    if inviter_id and inviter_id in user_data:
        inviter = user_data[inviter_id]
        before = inviter.get("diamonds", 0)
        inviter["diamonds"] = clamp_points(inviter.get("diamonds", 0) + 5)
        after = inviter["diamonds"]
        logging.info(f"start: начислено 5 брильянтов пользователю {inviter_id} (было {before}, стало {after})")
        await bot.send_message(
            inviter_id,
            text=f"🎉 Твой друг перешёл по ссылке! +5 брильянтов 💎 (было {before} → {after})"
        )
    
    kb = InlineKeyboardBuilder()
    kb.button(text="💚 Хочу здоровье", callback_data="health")
    kb.button(text="💰 Хочу доход", callback_data="income")
    kb.adjust(2)
    
    logging.info(f"start: отправка главного меню пользователю {user_id}")
    await message.answer(
        "Выбери, что тебе важнее 👇",
        reply_markup=kb.as_markup()
    )
    logging.info(f"start: главное меню отправлено пользователю {user_id}")

# ===========================================================
# ВЕТКА — ХОЧУ ЗДОРОВЬЕ
# ===========================================================
@dp.callback_query(F.data == "health")
async def start_health(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_data[user_id]["branch"] = "health"
    
    # Показываем приветственное сообщение с объяснением игры
    kb = InlineKeyboardBuilder()
    kb.button(text="🔹 Да, поехали!", callback_data="start_health_game")
    kb.adjust(1)
    
    await callback.message.answer(
        "Привет! 🌞\n"
        "Хочешь узнать, насколько ты заботишься о своём здоровье и что поможет тебе чувствовать себя лучше?\n\n"
        "🎮 Это короткая игра-опрос «Твоя энергия и здоровье».\n"
        "За каждый ответ ты получаешь 💎 брильянт,\n"
        "а в конце сможешь обменять брильянты на ценный приз!\n\n"
        "Готов(а) начать? 🌱",
        reply_markup=kb.as_markup()
    )
    await callback.answer()

@dp.callback_query(F.data == "start_health_game")
async def start_health_game(callback: CallbackQuery, state: FSMContext):
    # Показываем анимационную ракету
    try:
        # ID популярного анимированного стикера с ракетой
        rocket_sticker = "CAACAgIAAxkBAAICXmZ-xSjm9vQ0KnBxd3AAAbvxI8VPqwACJxYAAlQ_6EsAAeq7AZFX3fI0BA"
        await callback.message.answer_sticker(sticker=rocket_sticker)
    except:
        # Если стикер не загрузится, показываем эмодзи ракету
        await callback.message.answer("🚀")
    
    await asyncio.sleep(1.5)
    
    await callback.message.answer("👉 Напиши своё имя")
    await state.set_state(HealthForm.name)
    await callback.answer()

@dp.message(HealthForm.name)
async def health_name(message: Message, state: FSMContext):
    uid = message.from_user.id
    name = message.text.strip()
    
    # Валидация: только буквы (русские, английские, пробелы, дефис)
    if not name.replace(" ", "").replace("-", "").isalpha():
        await message.answer(
            "❌ Имя должно содержать только буквы!\n"
            "Попробуй еще раз. Напиши своё имя:"
        )
        return
    
    user_data[uid]["answers"]["name"] = name
    user_data[uid]["name"] = name
    user_data[uid]["diamonds"] += 1
    
    # Брильянт - задержка перед показом
    await asyncio.sleep(0.7)
    await message.answer("\n\n\n          💎\n\n\n")
    
    await asyncio.sleep(1)
    motivational_msg = await message.answer(
        "Мы рады приветствовать тебя в нашей игре! 🎮"
    )
    
    await asyncio.sleep(3)
    await motivational_msg.delete()
    
    await message.answer("👉 Напиши свой возраст")
    await state.set_state(HealthForm.age)

@dp.message(HealthForm.age)
async def health_age(message: Message, state: FSMContext):
    uid = message.from_user.id
    age = message.text.strip()
    
    # Валидация: только цифры
    if not age.isdigit():
        await message.answer(
            "❌ Возраст должен быть числом!\n"
            "Попробуй еще раз. Напиши свой возраст:"
        )
        return

    # Проверка разумности возраста
    if int(age) < 10 or int(age) > 120:
        await message.answer(
            "❌ Укажи реальный возраст (от 10 до 120 лет)!\n"
            "Попробуй еще раз. Напиши свой возраст:"
        )
        return

    user_data[uid]["answers"]["age"] = age
    user_data[uid]["diamonds"] += 1
    
    # Брильянт - задержка перед показом
    await asyncio.sleep(0.7)
    await message.answer("\n\n\n          💎\n\n\n")
    
    await asyncio.sleep(1)
    motivational_msg = await message.answer(
        "Возраст — это просто цифра, а настоящая сила в энергии 💪\n"
        "Двигаемся дальше 👇"
    )
    
    await asyncio.sleep(3)
    await motivational_msg.delete()
    
    # Вопрос про пол сразу после возраста
    kb = InlineKeyboardBuilder()
    kb.button(text="👩 Женщина", callback_data="h_gender_f")
    kb.button(text="👨 Мужчина", callback_data="h_gender_m")
    kb.adjust(2)
    
    await message.answer("🙂 Кто ты?", reply_markup=kb.as_markup())
    await state.set_state(HealthForm.gender)

@dp.callback_query(F.data.startswith("h_gender_"))
async def health_gender_after_age(callback: CallbackQuery, state: FSMContext):
    uid = callback.from_user.id
    gender = "Женщина" if callback.data.endswith("_f") else "Мужчина"
    user_data[uid]["answers"]["gender"] = gender
    user_data[uid]["gender"] = gender
    user_data[uid]["diamonds"] += 1
    
    # Брильянт - задержка перед показом
    await asyncio.sleep(0.7)
    await callback.message.answer("\n\n\n          💎\n\n\n")
    
    await asyncio.sleep(1)
    motivational_msg = await callback.message.answer(
        "Давай узнаем тебя получше 👇"
    )
    
    await asyncio.sleep(3)
    await motivational_msg.delete()
    
    await callback.message.answer("👉 Напиши свой рост (в см)")
    await state.set_state(HealthForm.height)
    await callback.answer()

@dp.message(HealthForm.height)
async def health_height(message: Message, state: FSMContext):
    uid = message.from_user.id
    height = message.text.strip()
    
    # Валидация: только цифры
    if not height.isdigit():
        await message.answer(
            "❌ Рост должен быть числом (в см)!\n"
            "Попробуй еще раз. Напиши свой рост:"
        )
        return

    # Проверка разумности роста (100-250 см)
    if int(height) < 100 or int(height) > 250:
        await message.answer(
            "❌ Укажи реальный рост (от 100 до 250 см)!\n"
            "Попробуй еще раз. Напиши свой рост:"
        )
        return
    
    user_data[uid]["answers"]["height"] = height
    user_data[uid]["diamonds"] += 1
    
    # Брильянт - задержка перед показом
    await asyncio.sleep(0.7)
    await message.answer("\n\n\n          💎\n\n\n")
    
    await asyncio.sleep(1)
    motivational_msg = await message.answer(
        "Отлично! Продолжаем узнавать тебя лучше 📊"
    )
    
    await asyncio.sleep(3)
    await motivational_msg.delete()
    
    await message.answer("👉 Напиши свой вес (в кг)")
    await state.set_state(HealthForm.weight)

@dp.message(HealthForm.weight)
async def health_weight(message: Message, state: FSMContext):
    uid = message.from_user.id
    weight = message.text.strip()
    
    # Валидация: только цифры
    if not weight.isdigit():
        await message.answer(
            "❌ Вес должен быть числом (в кг)!\n"
            "Попробуй еще раз. Напиши свой вес:"
        )
        return
    
    # Проверка разумности веса (30-300 кг)
    if int(weight) < 30 or int(weight) > 300:
        await message.answer(
            "❌ Укажи реальный вес (от 30 до 300 кг)!\n"
            "Попробуй еще раз. Напиши свой вес:"
        )
        return

    user_data[uid]["answers"]["weight"] = weight
    user_data[uid]["diamonds"] += 1
    
    # Брильянт - задержка перед показом
    await asyncio.sleep(0.7)
    await message.answer("\n\n\n          💎\n\n\n")
    
    await asyncio.sleep(1)
    motivational_msg = await message.answer(
        "Супер! Теперь давай определим твою цель 🎯"
    )
    
    await asyncio.sleep(3)
    await motivational_msg.delete()
    
    kb = InlineKeyboardBuilder()
    kb.button(text="⚡ Энергия", callback_data="h_goal_energy")
    kb.button(text="🛡 Иммунитет", callback_data="h_goal_immune")
    kb.button(text="😴 Сон", callback_data="h_goal_sleep")
    kb.button(text="🏃 Похудение", callback_data="h_goal_fit")
    kb.adjust(2)
    
    await message.answer("Выбери свою цель 🎯", reply_markup=kb.as_markup())
    await state.clear()

@dp.callback_query(F.data.startswith("h_goal_"))
async def health_goal(callback: CallbackQuery):
    uid = callback.from_user.id
    goal = callback.data.split("_")[-1]
    user_data[uid]["answers"]["goal"] = callback.data
    user_data[uid]["diamonds"] += 1
    
    # Брильянт - задержка перед показом
    await asyncio.sleep(0.7)
    await callback.message.answer("\n\n\n          💎\n\n\n")
    
    await asyncio.sleep(1)
    motivational_msg = await callback.message.answer(
        "Отличная цель! Здоровье — это основа всего 💪"
    )
    
    await asyncio.sleep(3)
    await motivational_msg.delete()
    
    # Начинаем блок вопросов про питание
    kb = InlineKeyboardBuilder()
    kb.button(text="🥤 1 л", callback_data="water_1")
    kb.button(text="💧 1.5 л", callback_data="water_1_5")
    kb.button(text="💦 2 л", callback_data="water_2")
    kb.button(text="🌊 3 л+", callback_data="water_3")
    kb.adjust(2)
    
    await callback.message.answer(
        "💧 Сколько воды ты пьёшь в день?",
        reply_markup=kb.as_markup()
    )
    await callback.answer()

# Вопрос 1: Сколько воды пьёшь
@dp.callback_query(F.data.startswith("water_"))
async def health_water(callback: CallbackQuery):
    uid = callback.from_user.id
    user_data[uid]["answers"]["water"] = callback.data
    user_data[uid]["diamonds"] += 1
    
    # Брильянт - задержка перед показом
    await asyncio.sleep(0.7)
    await callback.message.answer("\n\n\n          💎\n\n\n")
    
    await asyncio.sleep(1)
    motivational_msg = await callback.message.answer(
        "Вода — основа жизни! Отличное начало 💧"
    )
    
    await asyncio.sleep(3)
    await motivational_msg.delete()
    
    kb = InlineKeyboardBuilder()
    kb.button(text="🥩 Мясо", callback_data="food_meat")
    kb.button(text="🐟 Рыбу", callback_data="food_fish")
    kb.button(text="🍣 Суши", callback_data="food_sushi")
    kb.button(text="🥗 Вегетарианец", callback_data="food_veg")
    kb.adjust(2)
    
    await callback.message.answer(
        "🍖 Что чаще ешь?",
        reply_markup=kb.as_markup()
    )
    await callback.answer()

# Вопрос 2: Что чаще ешь
@dp.callback_query(F.data.startswith("food_"))
async def health_food(callback: CallbackQuery):
    uid = callback.from_user.id
    food_choice = callback.data
    user_data[uid]["answers"]["food"] = food_choice
    user_data[uid]["diamonds"] += 1
    
    # Брильянт - задержка перед показом
    await asyncio.sleep(0.7)
    await callback.message.answer("\n\n\n          💎\n\n\n")
    
    await asyncio.sleep(1)
    motivational_msg = await callback.message.answer(
        "Отличный выбор! Питание — ключ к здоровью 🍽"
    )
    
    await asyncio.sleep(3)
    await motivational_msg.delete()
    
    # Если выбрал вегетарианец - пропускаем вопрос про частоту
    if food_choice == "food_veg":
        kb = InlineKeyboardBuilder()
        kb.button(text="🥦 Каждый день", callback_data="veg_daily")
        kb.button(text="🥒 Иногда", callback_data="veg_sometimes")
        kb.button(text="🍅 Редко", callback_data="veg_rare")
        kb.button(text="🚫 Не ем", callback_data="veg_no")
        kb.adjust(2)
        
        await callback.message.answer(
            "🥕 Ешь овощи?",
            reply_markup=kb.as_markup()
        )
        await callback.answer()
        return

    # Для мяса, рыбы, суши - спрашиваем частоту
    food_name = {
        "food_meat": "мясо",
        "food_fish": "рыбу",
        "food_sushi": "суши"
    }.get(food_choice, "это")
    
    kb = InlineKeyboardBuilder()
    kb.button(text="🍽 Каждый день", callback_data=f"eat_{food_choice}_day")
    kb.button(text="🗓 Раз в неделю", callback_data=f"eat_{food_choice}_week")
    kb.button(text="📅 Раз в месяц", callback_data=f"eat_{food_choice}_month")
    kb.button(text="🌱 Почти не ем", callback_data=f"eat_{food_choice}_never")
    kb.adjust(2)
    
    await callback.message.answer(
        f"Как часто ешь {food_name}?",
        reply_markup=kb.as_markup()
    )
    await callback.answer()

# Вопрос 3: Как часто ешь мясо/рыбу/суши
@dp.callback_query(F.data.startswith("eat_food_"))
async def health_freq(callback: CallbackQuery):
    uid = callback.from_user.id
    user_data[uid]["answers"]["eat_freq"] = callback.data
    user_data[uid]["diamonds"] += 1
    
    # Брильянт - задержка перед показом
    await asyncio.sleep(0.7)
    await callback.message.answer("\n\n\n          💎\n\n\n")
    
    await asyncio.sleep(1)
    motivational_msg = await callback.message.answer(
        "Баланс в питании — залог энергии 🔋"
    )
    
    await asyncio.sleep(3)
    await motivational_msg.delete()
    
    kb = InlineKeyboardBuilder()
    kb.button(text="🥦 Каждый день", callback_data="veg_daily")
    kb.button(text="🥒 Иногда", callback_data="veg_sometimes")
    kb.button(text="🍅 Редко", callback_data="veg_rare")
    kb.button(text="🚫 Не ем", callback_data="veg_no")
    kb.adjust(2)
    
    await callback.message.answer(
        "🥕 Ешь овощи?",
        reply_markup=kb.as_markup()
    )
    await callback.answer()

# Вопрос 4: Ешь овощи
@dp.callback_query(F.data.startswith("veg_"))
async def health_veg(callback: CallbackQuery):
    uid = callback.from_user.id
    user_data[uid]["answers"]["vegetables"] = callback.data
    user_data[uid]["diamonds"] += 1
    
    # Брильянт - задержка перед показом
    await asyncio.sleep(0.7)
    await callback.message.answer("\n\n\n          💎\n\n\n")
    
    await asyncio.sleep(1)
    motivational_msg = await callback.message.answer(
        "Овощи — это витамины и энергия! 🥦"
    )
    
    await asyncio.sleep(3)
    await motivational_msg.delete()
    
    kb = InlineKeyboardBuilder()
    kb.button(text="🌿 Каждый день", callback_data="green_daily")
    kb.button(text="🌱 Иногда", callback_data="green_sometimes")
    kb.button(text="🍃 Редко", callback_data="green_rare")
    kb.button(text="🚫 Нет", callback_data="green_no")
    kb.adjust(2)
    
    await callback.message.answer(
        "🌿 Кушаешь зелень?",
        reply_markup=kb.as_markup()
    )
    await callback.answer()

# Вопрос 5: Кушаешь зелень
@dp.callback_query(F.data.startswith("green_"))
async def health_green(callback: CallbackQuery):
    uid = callback.from_user.id
    user_data[uid]["answers"]["greens"] = callback.data
    user_data[uid]["diamonds"] += 1
    
    # Брильянт - задержка перед показом
    await asyncio.sleep(0.7)
    await callback.message.answer("\n\n\n          💎\n\n\n")
    
    await asyncio.sleep(1)
    motivational_msg = await callback.message.answer(
        "Зелень — природный детокс! 🌿"
    )
    
    await asyncio.sleep(3)
    await motivational_msg.delete()
    
    # Новый вопрос про кофе/чай
    kb = InlineKeyboardBuilder()
    kb.button(text="☕ Кофе", callback_data="drink_coffee")
    kb.button(text="🍵 Чай", callback_data="drink_tea")
    kb.button(text="🚫 Не пью", callback_data="drink_no")
    kb.button(text="🥤 Другое", callback_data="drink_other")
    kb.adjust(2)
    
    await callback.message.answer(
        "☕ Пьешь кофе или чай?",
        reply_markup=kb.as_markup()
    )
    await callback.answer()

# Вопрос 6: Пьешь кофе или чай
@dp.callback_query(F.data.startswith("drink_"))
async def health_drink(callback: CallbackQuery):
    uid = callback.from_user.id
    drink_choice = callback.data
    user_data[uid]["answers"]["drink"] = drink_choice
    user_data[uid]["diamonds"] += 1
    
    # Брильянт - задержка перед показом
    await asyncio.sleep(0.7)
    await callback.message.answer("\n\n\n          💎\n\n\n")
    
    await asyncio.sleep(1)
    motivational_msg = await callback.message.answer(
        "Твои привычки формируют твоё здоровье ☕"
    )
    
    await asyncio.sleep(3)
    await motivational_msg.delete()
    
    # Если выбрал "Не пью" или "Другое" - пропускаем вопрос про частоту
    if drink_choice in ["drink_no", "drink_other"]:
        # Сразу переходим к вопросу про витамины
        kb = InlineKeyboardBuilder()
        kb.button(text="✅ Да, регулярно", callback_data="vitamins_regular")
        kb.button(text="🔄 Иногда", callback_data="vitamins_sometimes")
        kb.button(text="⏰ Редко", callback_data="vitamins_rare")
        kb.button(text="❌ Никогда", callback_data="vitamins_never")
        kb.adjust(2)
        
        await callback.message.answer(
            "💊 Принимаешь витамины/БАДы?",
            reply_markup=kb.as_markup()
        )
        await callback.answer()
        return
    
    # Для кофе или чая - спрашиваем частоту
    drink_name = {
        "drink_coffee": "кофе",
        "drink_tea": "чай"
    }.get(drink_choice, "это")
    
    kb = InlineKeyboardBuilder()
    kb.button(text="☕ Каждый день", callback_data=f"drinkfreq_{drink_choice}_day")
    kb.button(text="🗓 Раз в неделю", callback_data=f"drinkfreq_{drink_choice}_week")
    kb.button(text="📅 Раз в месяц", callback_data=f"drinkfreq_{drink_choice}_month")
    kb.button(text="🚫 Почти не пью", callback_data=f"drinkfreq_{drink_choice}_never")
    kb.adjust(2)
    
    await callback.message.answer(
        f"☕ Как часто пьешь {drink_name}?",
        reply_markup=kb.as_markup()
    )
    await callback.answer()

# Вопрос 6.5: Как часто пьешь кофе/чай
@dp.callback_query(F.data.startswith("drinkfreq_"))
async def health_drink_freq(callback: CallbackQuery):
    uid = callback.from_user.id
    user_data[uid]["answers"]["drink_freq"] = callback.data
    user_data[uid]["diamonds"] += 1
    
    # Брильянт - задержка перед показом
    await asyncio.sleep(0.7)
    await callback.message.answer("\n\n\n          💎\n\n\n")
    
    await asyncio.sleep(1)
    motivational_msg = await callback.message.answer(
        "Знать свои привычки — первый шаг к улучшению 📈"
    )
    
    await asyncio.sleep(3)
    await motivational_msg.delete()
    
    # Вопрос про витамины/БАДы
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Да, регулярно", callback_data="vitamins_regular")
    kb.button(text="🔄 Иногда", callback_data="vitamins_sometimes")
    kb.button(text="⏰ Редко", callback_data="vitamins_rare")
    kb.button(text="❌ Никогда", callback_data="vitamins_never")
    kb.adjust(2)
    
    await callback.message.answer(
        "💊 Принимаешь витамины/БАДы?",
        reply_markup=kb.as_markup()
    )
    await callback.answer()

# Вопрос 7: Принимаешь витамины/БАДы
@dp.callback_query(F.data.startswith("vitamins_"))
async def health_vitamins(callback: CallbackQuery):
    try:
        uid = callback.from_user.id
        logging.info(f"health_vitamins: вызван для пользователя {uid}, ответ: {callback.data}")
        user_data[uid]["answers"]["vitamins"] = callback.data
        user_data[uid]["diamonds"] += 1
        logging.info(f"health_vitamins: брильянты для {uid} = {user_data[uid]['diamonds']}")
        
        # Брильянт - задержка перед показом
        await asyncio.sleep(0.7)
        await callback.message.answer("\n\n\n          💎\n\n\n")
        
        await asyncio.sleep(1)
        motivational_msg = await callback.message.answer(
            "Витамины — твоя поддержка изнутри! 💊\n"
            "Последний шаг 👇"
        )
        
        await asyncio.sleep(3)
        await motivational_msg.delete()
        
        # Финал блока - предложение подписаться с переходом в канал
        total = user_data[uid]["diamonds"]
        logging.info(f"health_vitamins: показ блока подписки для {uid}, брильянтов: {total}")
        
        # Показываем URL-кнопку для подписки на канал
        kb = InlineKeyboardBuilder()
        if CHANNEL_URL:
            kb.button(text="🔔 Подписаться на канал", url=CHANNEL_URL)
            kb.adjust(1)
            button_text = "👇 Нажми на кнопку ниже, чтобы подписаться:"
            logging.info(f"health_vitamins: отправка сообщения с кнопкой подписки для {uid}, URL: {CHANNEL_URL}")
        else:
            logging.error(f"health_vitamins: CHANNEL_URL не установлен для пользователя {uid}")
            button_text = ""
        
        msg = await callback.message.answer(
            f"💎 Отлично! Ты прошёл оздоровительный блок.\n"
            f"У тебя сейчас {total} брильянтов 🌟\n\n"
            "🔔 Подпишись на наш канал!\n"
            "💎 После подписки общее количество брильянтов будет равно 19!\n\n"
            f"{button_text}",
            reply_markup=kb.as_markup() if CHANNEL_URL else None
        )
        await callback.answer()
        logging.info(f"health_vitamins: сообщение с кнопкой подписки отправлено для {uid}")
        
        # Ждем 6 секунд и автоматически показываем кнопку ПРОДОЛЖИТЬ
        logging.info(f"health_vitamins: ожидание 6 секунд перед показом кнопки ПРОДОЛЖИТЬ для {uid}")
        await asyncio.sleep(6)
        
        kb2 = InlineKeyboardBuilder()
        kb2.button(text="✅ ПРОДОЛЖИТЬ ✅", callback_data="h_sub")
        kb2.adjust(1)
        
        logging.info(f"health_vitamins: отправка кнопки ПРОДОЛЖИТЬ для {uid}")
        await callback.message.answer(
            "✅ После подписки нажми ПРОДОЛЖИТЬ:",
            reply_markup=kb2.as_markup()
        )
        logging.info(f"health_vitamins: кнопка ПРОДОЛЖИТЬ отправлена для {uid}")
    except Exception as e:
        logging.error(f"Ошибка в health_vitamins: {e}")
        await callback.answer("Произошла ошибка, попробуйте позже", show_alert=True)

# Старый обработчик пола удален, теперь пол спрашивается после возраста

@dp.callback_query(F.data == "h_sub")
async def health_sub(callback: CallbackQuery):
    uid = callback.from_user.id
    logging.info(f"health_sub: вызван для пользователя {uid}")
    
    # Проверяем подписку на канал
    logging.info(f"health_sub: проверка подписки для {uid}")
    is_subscribed = await check_subscription(uid)
    logging.info(f"health_sub: результат проверки подписки для {uid} = {is_subscribed}")
    
    if not is_subscribed:
        # Если не подписан - показываем предупреждение
        await callback.answer(
            "⚠️ Сначала подпишись на канал!",
            show_alert=True
        )
        
        # Дополнительное сообщение с напоминанием
        kb = InlineKeyboardBuilder()
        if not CHANNEL_URL:
            logging.error(f"health_sub: CHANNEL_URL не установлен для пользователя {uid}")
            channel_text = "Пожалуйста, подпишись на канал!\n\n"
        else:
            kb.button(text="🔔 Подписаться на канал", url=CHANNEL_URL)
            channel_text = f"Пожалуйста, подпишись на канал:\n{CHANNEL_URL}\n\n"
        kb.button(text="━━━━━━━━  ✅ ПРОДОЛЖИТЬ ✅  ━━━━━━━━", callback_data="h_sub")
        kb.adjust(1)
        
        await callback.message.answer(
            "❌ Подписка не обнаружена!\n\n"
            f"{channel_text}"
            "После подписки нажми кнопку 'ПРОДОЛЖИТЬ' снова",
            reply_markup=kb.as_markup()
        )
        return
    
    # Если подписан - продолжаем
    user_data[uid]["diamonds"] = clamp_points(user_data[uid]["diamonds"] + 5)
    
    send_to_amocrm(uid)
    
    # 1. Анимационное конфетти
    try:
        confetti_boom = "CAACAgIAAxkBAAICW2Z-xQjOqTx9AAE3QfEHj6wVNf3YNQACMhYAAlQ_6Eu9D4QAAYvQoiw0BA"
        await callback.message.answer_sticker(sticker=confetti_boom)
    except:
        await callback.message.answer("🎊")
    
    await asyncio.sleep(1.5)
    
    # 2. Анимационный кубок
    try:
        trophy_sticker = "CAACAgIAAxkBAAICXGZ-xRJkf0OQdHLGb_xQJXhXYKSVAAIkFgACVD_oS1zZnwAB-FS51jQE"
        await callback.message.answer_sticker(sticker=trophy_sticker)
    except:
        await callback.message.answer("🏆")
    
    await asyncio.sleep(1.5)
    
    # 3. Первое сообщение: Вы выиграли + баланс
    # В ветке "Хочу здоровье" после подписки всегда 19 брильянтов (20-й только после приглашения друга)
    await callback.message.answer(
        f"🎉 ВЫ ВЫИГРАЛИ! 🎉\n\n"
        f"💎 У вас 19 брильянтов 💎"
    )
    
    await asyncio.sleep(2)
    
    # 4. Второе сообщение с призывом пригласить друга (показывается 6 секунд)
    invite_msg = await callback.message.answer(
        "🎁 Подарок уже почти твой!\n\n"
        "> Для него тебе нужен всего один бриллиант 💎\n\n"
        "👥 Просто пригласи одного друга в путешествие Coral Quest —\n"
        "> и получи свой заслуженный приз вместе с новыми впечатлениями! 🌟"
    )
    
    await asyncio.sleep(6)
    
    # 5. Удаляем предыдущее сообщение
    await invite_msg.delete()
    
    # 6. Анимационная рука показывает вниз
    await callback.message.answer("👇")
    
    await asyncio.sleep(1)
    
    # 7. Первые кнопки: Пригласить друга и Баланс
    kb = InlineKeyboardBuilder()
    kb.button(text="👥 Пригласить друга", callback_data="invite")
    kb.button(text="💰 Мой баланс", callback_data="balance")
    kb.adjust(1)
    
    await callback.message.answer(
        "👇 Выбери действие:",
        reply_markup=kb.as_markup()
    )
    
    await callback.answer()

# ===========================================================
# ВЕТКА — ХОЧУ ДОХОД
# ===========================================================
@dp.callback_query(F.data == "income")
async def start_income(callback: CallbackQuery, state: FSMContext):
    uid = callback.from_user.id
    user_data[uid]["branch"] = "income"
    user_data[uid]["answers"] = {}
    
    # Приветственное сообщение
    welcome_text = (
        "Привет! 👋\n\n"
        "Сейчас мы узнаем, какие у тебя сильные стороны в работе и в чём твоя зона роста.\n\n"
        "За каждый ответ ты получаешь 💎 брильянт осознанности.\n\n"
        "🎁 Собери 20 брильянтов и обменяй их на ценный приз!\n\n"
        "Готов(а) начать?"
    )
    
    kb = InlineKeyboardBuilder()
    kb.button(text="━━━━━━━  Да, поехали! 🚀  ━━━━━━━", callback_data="income_start")
    kb.adjust(1)
    
    await callback.message.answer(welcome_text, reply_markup=kb.as_markup())
    await state.set_state(IncomeForm.welcome)
    await callback.answer()

@dp.callback_query(F.data == "income_start")
async def start_income_game(callback: CallbackQuery, state: FSMContext):
    # Анимация ракеты
    await callback.message.answer("🚀")
    await asyncio.sleep(1)
    
    await callback.message.answer("👉 Напиши своё имя")
    await state.set_state(IncomeForm.name)
    await callback.answer()

# --------------------------------------------------------------------------
# ВЕТКА: ДОХОД - Обработчики
# --------------------------------------------------------------------------

@dp.message(IncomeForm.name)
async def income_name(message: Message, state: FSMContext):
    uid = message.from_user.id
    name = message.text.strip()
    
    # Валидация: только буквы (русские, английские, пробелы, дефис)
    if not name.replace(" ", "").replace("-", "").isalpha():
        await message.answer(
            "❌ Имя должно содержать только буквы!\n"
            "Попробуй еще раз. Напиши своё имя:"
        )
        return
    
    user_data[uid]["answers"]["name"] = name
    user_data[uid]["name"] = name
    user_data[uid]["diamonds"] += 1
    
    # Брильянт
    await asyncio.sleep(0.7)
    await message.answer("\n\n\n          💎\n\n\n")
    
    await asyncio.sleep(1)
    motivational_msg = await message.answer(
        "Мы рады приветствовать тебя в нашей игре! 🎮"
    )
    
    await asyncio.sleep(3)
    await motivational_msg.delete()
    
    await message.answer("👉 Напиши свой возраст")
    await state.set_state(IncomeForm.age)

@dp.message(IncomeForm.age)
async def income_age(message: Message, state: FSMContext):
    uid = message.from_user.id
    age = message.text.strip()
    
    # Валидация: только цифры
    if not age.isdigit():
        await message.answer(
            "❌ Возраст должен быть числом!\n"
            "Попробуй еще раз. Напиши свой возраст:"
        )
        return

    # Проверка разумности возраста
    if int(age) < 10 or int(age) > 120:
        await message.answer(
            "❌ Укажи реальный возраст (от 10 до 120 лет)!\n"
            "Попробуй еще раз. Напиши свой возраст:"
        )
        return

    user_data[uid]["answers"]["age"] = age
    user_data[uid]["diamonds"] += 1
    
    # Брильянт
    await asyncio.sleep(0.7)
    await message.answer("\n\n\n          💎\n\n\n")
    
    await asyncio.sleep(1)
    motivational_msg = await message.answer(
        "Возраст — это просто цифра, а настоящая сила в энергии 💪\n"
        "Двигаемся дальше 👇"
    )
    
    await asyncio.sleep(3)
    await motivational_msg.delete()
    
    # Вопрос про пол сразу после возраста
    kb = InlineKeyboardBuilder()
    kb.button(text="👩 Женщина", callback_data="inc_gender_after_age_f")
    kb.button(text="👨 Мужчина", callback_data="inc_gender_after_age_m")
    kb.adjust(2)
    
    await message.answer("Выбери свой пол:", reply_markup=kb.as_markup())
    await state.set_state(IncomeForm.gender)

@dp.callback_query(F.data.startswith("inc_gender_after_age_"))
async def income_gender_after_age(callback: CallbackQuery, state: FSMContext):
    uid = callback.from_user.id
    gender = "Женщина" if callback.data.endswith("_f") else "Мужчина"
    user_data[uid]["answers"]["gender"] = gender
    user_data[uid]["gender"] = gender
    user_data[uid]["diamonds"] += 1
    
    # Брильянт - задержка перед показом
    await asyncio.sleep(0.7)
    await callback.message.answer("\n\n\n          💎\n\n\n")
    
    await asyncio.sleep(1)
    motivational_msg = await callback.message.answer(
        "Давай узнаем тебя получше 👇"
    )
    
    await asyncio.sleep(3)
    await motivational_msg.delete()
    
    # Теперь спрашиваем про доход
    kb = InlineKeyboardBuilder()
    kb.button(text="💵 До 100 000 ₽", callback_data="income_100k")
    kb.button(text="💰 200 000 ₽+", callback_data="income_200k")
    kb.button(text="💎 500 000 ₽+", callback_data="income_500k")
    kb.button(text="🚀 1 млн+", callback_data="income_1m")
    kb.adjust(2)
    
    await callback.message.answer(
        "3️⃣ Какой доход ты хочешь получать?",
        reply_markup=kb.as_markup()
    )
    await state.set_state(IncomeForm.desired_income)
    await callback.answer()

@dp.callback_query(F.data.startswith("income_") & F.data.in_(["income_100k", "income_200k", "income_500k", "income_1m"]))
async def income_desired(callback: CallbackQuery, state: FSMContext):
    uid = callback.from_user.id
    
    income_map = {
        "income_100k": "До 100 000 ₽",
        "income_200k": "200 000 ₽+",
        "income_500k": "500 000 ₽+",
        "income_1m": "1 млн+"
    }
    
    user_data[uid]["answers"]["desired_income"] = income_map.get(callback.data, "не указано")
    user_data[uid]["diamonds"] += 1
    
    # Брильянт
    await asyncio.sleep(0.7)
    await callback.message.answer("\n\n\n          💎\n\n\n")
    
    await asyncio.sleep(1)
    motivational_msg = await callback.message.answer(
        "Отличная цель, амбиции — основа роста!"
    )
    
    await asyncio.sleep(3)
    await motivational_msg.delete()
    
    kb = InlineKeyboardBuilder()
    kb.button(text="🏠 Онлайн", callback_data="format_online")
    kb.button(text="🏢 Офлайн", callback_data="format_offline")
    kb.button(text="🌍 Оба формата", callback_data="format_both")
    kb.adjust(1)
    
    await callback.message.answer(
        "4️⃣ Где тебе комфортнее работать?",
        reply_markup=kb.as_markup()
    )
    await state.set_state(IncomeForm.work_format)
    await callback.answer()

@dp.callback_query(F.data.startswith("format_"))
async def income_work_format(callback: CallbackQuery, state: FSMContext):
    uid = callback.from_user.id
    
    format_map = {
        "format_online": "Онлайн",
        "format_offline": "Офлайн",
        "format_both": "Оба формата"
    }
    
    user_data[uid]["answers"]["work_format"] = format_map.get(callback.data, "не указано")
    user_data[uid]["diamonds"] += 1
    
    # Брильянт
    await asyncio.sleep(0.7)
    await callback.message.answer("\n\n\n          💎\n\n\n")
    
    await asyncio.sleep(1)
    motivational_msg = await callback.message.answer(
        "Класс, важно понимать свою зону комфорта 💫"
    )
    
    await asyncio.sleep(3)
    await motivational_msg.delete()
    
    kb = InlineKeyboardBuilder()
    kb.button(text="👥 В команде", callback_data="style_team")
    kb.button(text="🧍‍♀️ Самостоятельно", callback_data="style_solo")
    kb.button(text="⚖️ И так, и так", callback_data="style_both")
    kb.adjust(1)
    
    await callback.message.answer(
        "5️⃣ Как тебе нравится работать?",
        reply_markup=kb.as_markup()
    )
    await state.set_state(IncomeForm.work_style)
    await callback.answer()

@dp.callback_query(F.data.startswith("style_"))
async def income_work_style(callback: CallbackQuery, state: FSMContext):
    uid = callback.from_user.id
    
    style_map = {
        "style_team": "В команде",
        "style_solo": "Самостоятельно",
        "style_both": "И так, и так"
    }
    
    user_data[uid]["answers"]["work_style"] = style_map.get(callback.data, "не указано")
    user_data[uid]["diamonds"] += 1
    
    # Брильянт
    await asyncio.sleep(0.7)
    await callback.message.answer("\n\n\n          💎\n\n\n")
    
    await asyncio.sleep(1)
    motivational_msg = await callback.message.answer(
        "Настоящий баланс формируется, когда понимаешь свои сильные стороны ⚙️"
    )
    
    await asyncio.sleep(3)
    await motivational_msg.delete()
    
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Да", callback_data="exp_yes")
    kb.button(text="💡 Навыки есть", callback_data="exp_some")
    kb.button(text="🆕 Начинаю", callback_data="exp_start")
    kb.button(text="❓ Пробую", callback_data="exp_try")
    kb.adjust(2)
    
    await callback.message.answer(
        "6️⃣ Есть ли у тебя опыт в своём деле или бизнесе?",
        reply_markup=kb.as_markup()
    )
    await state.set_state(IncomeForm.experience)
    await callback.answer()

@dp.callback_query(F.data.startswith("exp_"))
async def income_experience(callback: CallbackQuery, state: FSMContext):
    uid = callback.from_user.id
    
    exp_map = {
        "exp_yes": "Да",
        "exp_some": "Навыки есть",
        "exp_start": "Начинаю",
        "exp_try": "Пробую"
    }
    
    user_data[uid]["answers"]["experience"] = exp_map.get(callback.data, "не указано")
    user_data[uid]["diamonds"] += 1
    
    # Брильянт
    await asyncio.sleep(0.7)
    await callback.message.answer("\n\n\n          💎\n\n\n")
    
    await asyncio.sleep(1)
    motivational_msg = await callback.message.answer(
        "Каждый стартует с разного уровня — главное делать шаги вперёд 🔥"
    )
    
    await asyncio.sleep(3)
    await motivational_msg.delete()
    
    kb = InlineKeyboardBuilder()
    kb.button(text="📱 Продажи", callback_data="sphere_sales")
    kb.button(text="💻 Маркетинг", callback_data="sphere_marketing")
    kb.button(text="🧑‍🏫 Обучение", callback_data="sphere_education")
    kb.button(text="🧘‍♀️ Wellness", callback_data="sphere_wellness")
    kb.button(text="🏗 Услуги", callback_data="sphere_services")
    kb.button(text="💬 Другое", callback_data="sphere_other")
    kb.adjust(2)
    
    await callback.message.answer(
        "7️⃣ В какой сфере ты сейчас?",
        reply_markup=kb.as_markup()
    )
    await state.set_state(IncomeForm.sphere)
    await callback.answer()

@dp.callback_query(F.data.startswith("sphere_"))
async def income_sphere(callback: CallbackQuery, state: FSMContext):
    uid = callback.from_user.id
    
    sphere_map = {
        "sphere_sales": "Продажи",
        "sphere_marketing": "Маркетинг",
        "sphere_education": "Обучение",
        "sphere_wellness": "Wellness",
        "sphere_services": "Услуги",
        "sphere_other": "Другое"
    }
    
    user_data[uid]["answers"]["sphere"] = sphere_map.get(callback.data, "не указано")
    user_data[uid]["diamonds"] += 1
    
    # Брильянт
    await asyncio.sleep(0.7)
    await callback.message.answer("\n\n\n          💎\n\n\n")
    
    await asyncio.sleep(1)
    motivational_msg = await callback.message.answer(
        "Любая сфера — трамплин, если использовать её опыт мудро 💫"
    )
    
    await asyncio.sleep(3)
    await motivational_msg.delete()
    
    kb = InlineKeyboardBuilder()
    kb.button(text="🎤 Коммуникация и продажи", callback_data="skills_comm")
    kb.button(text="👥 Управление командой", callback_data="skills_management")
    kb.button(text="🌐 Онлайн-навыки", callback_data="skills_online")
    kb.button(text="💰 Финансовое мышление", callback_data="skills_finance")
    kb.button(text="🧘‍♀️ Самоорганизация", callback_data="skills_self")
    kb.adjust(1)
    
    await callback.message.answer(
        "8️⃣ Какие навыки хочешь развить?",
        reply_markup=kb.as_markup()
    )
    await state.set_state(IncomeForm.skills)
    await callback.answer()

@dp.callback_query(F.data.startswith("skills_"))
async def income_skills(callback: CallbackQuery, state: FSMContext):
    uid = callback.from_user.id
    
    skills_map = {
        "skills_comm": "Коммуникация и продажи",
        "skills_management": "Управление командой",
        "skills_online": "Онлайн-навыки",
        "skills_finance": "Финансовое мышление",
        "skills_self": "Самоорганизация"
    }
    
    user_data[uid]["answers"]["skills"] = skills_map.get(callback.data, "не указано")
    user_data[uid]["diamonds"] += 1
    
    # Брильянт
    await asyncio.sleep(0.7)
    await callback.message.answer("\n\n\n          💎\n\n\n")
    
    await asyncio.sleep(1)
    motivational_msg = await callback.message.answer(
        "Прокачка начинается с осознания, куда двигаться 🎯"
    )
    
    await asyncio.sleep(3)
    await motivational_msg.delete()
    
    kb = InlineKeyboardBuilder()
    kb.button(text="⏰ 1–2 ч", callback_data="time_1_2")
    kb.button(text="🕒 3–4 ч", callback_data="time_3_4")
    kb.button(text="🌞 5+ ч", callback_data="time_5plus")
    kb.button(text="🪶 Посмотрим", callback_data="time_little")
    kb.adjust(2)
    
    await callback.message.answer(
        "9️⃣ Сколько времени готов(а) вкладывать в развитие в день?",
        reply_markup=kb.as_markup()
    )
    await state.set_state(IncomeForm.time_invest)
    await callback.answer()

@dp.callback_query(F.data.startswith("time_"))
async def income_time(callback: CallbackQuery, state: FSMContext):
    uid = callback.from_user.id
    
    time_map = {
        "time_1_2": "1–2 ч",
        "time_3_4": "3–4 ч",
        "time_5plus": "5+ ч",
        "time_little": "Посмотрим"
    }
    
    user_data[uid]["answers"]["time_invest"] = time_map.get(callback.data, "не указано")
    user_data[uid]["diamonds"] += 1
    
    # Брильянт
    await asyncio.sleep(0.7)
    await callback.message.answer("\n\n\n          💎\n\n\n")
    
    await asyncio.sleep(1)
    motivational_msg = await callback.message.answer(
        "Последовательность = результат 🔑"
    )
    
    await asyncio.sleep(3)
    await motivational_msg.delete()
    
    kb = InlineKeyboardBuilder()
    kb.button(text="🔑 Свобода", callback_data="values_freedom")
    kb.button(text="💰 Доход", callback_data="values_income")
    kb.button(text="🎯 Самореализация", callback_data="values_self")
    kb.button(text="🧡 Польза людям", callback_data="values_help")
    kb.button(text="⚖️ Баланс", callback_data="values_balance")
    kb.adjust(2)
    
    await callback.message.answer(
        "🔟 Что для тебя самое важное в работе?",
        reply_markup=kb.as_markup()
    )
    await state.set_state(IncomeForm.values)
    await callback.answer()

@dp.callback_query(F.data.startswith("values_"))
async def income_values(callback: CallbackQuery, state: FSMContext):
    uid = callback.from_user.id
    
    values_map = {
        "values_freedom": "Свобода",
        "values_income": "Доход",
        "values_self": "Самореализация",
        "values_help": "Польза людям",
        "values_balance": "Баланс"
    }
    
    user_data[uid]["answers"]["values"] = values_map.get(callback.data, "не указано")
    user_data[uid]["diamonds"] += 1
    
    # Брильянт
    await asyncio.sleep(0.7)
    await callback.message.answer("\n\n\n          💎\n\n\n")
    
    await asyncio.sleep(1)
    motivational_msg = await callback.message.answer(
        "Ценности — это топливо твоего пути 🚀"
    )
    
    await asyncio.sleep(3)
    await motivational_msg.delete()
    
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Да!", callback_data="ready_yes")
    kb.button(text="⏳ Готовлюсь", callback_data="ready_preparing")
    kb.button(text="📘 Изучаю", callback_data="ready_learning")
    kb.button(text="🤔 Думаю", callback_data="ready_thinking")
    kb.adjust(2)
    
    await callback.message.answer(
        "1️⃣1️⃣ Ты готов начать действовать прямо сейчас?",
        reply_markup=kb.as_markup()
    )
    await state.set_state(IncomeForm.ready_start)
    await callback.answer()

@dp.callback_query(F.data.startswith("ready_"))
async def income_ready(callback: CallbackQuery, state: FSMContext):
    uid = callback.from_user.id
    
    ready_map = {
        "ready_yes": "Да!",
        "ready_preparing": "Готовлюсь",
        "ready_learning": "Изучаю",
        "ready_thinking": "Думаю"
    }
    
    user_data[uid]["answers"]["ready_start"] = ready_map.get(callback.data, "не указано")
    user_data[uid]["diamonds"] += 1
    
    # Брильянт
    await asyncio.sleep(0.7)
    await callback.message.answer("\n\n\n          💎\n\n\n")
    
    await asyncio.sleep(1)
    motivational_msg = await callback.message.answer(
        "Отлично! Каждый шаг — ещё один уровень в игре 💎"
    )
    
    await asyncio.sleep(3)
    await motivational_msg.delete()
    
    kb = InlineKeyboardBuilder()
    kb.button(text="💡 План", callback_data="need_plan")
    kb.button(text="👥 Наставник", callback_data="need_mentor")
    kb.button(text="💻 Инструменты", callback_data="need_tools")
    kb.button(text="⏰ Время", callback_data="need_time")
    kb.button(text="🎯 Мотивация", callback_data="need_motivation")
    kb.adjust(2)
    
    await callback.message.answer(
        "1️⃣2️⃣ Что тебе нужно, чтобы начать уверенно?",
        reply_markup=kb.as_markup()
    )
    await state.set_state(IncomeForm.need_start)
    await callback.answer()

@dp.callback_query(F.data.startswith("need_"))
async def income_need(callback: CallbackQuery, state: FSMContext):
    try:
        uid = callback.from_user.id
        logging.info(f"income_need: вызван для пользователя {uid}, ответ: {callback.data}")
        
        need_map = {
            "need_plan": "План",
            "need_mentor": "Наставник",
            "need_tools": "Инструменты",
            "need_time": "Время",
            "need_motivation": "Мотивация"
        }
        
        user_data[uid]["answers"]["need_start"] = need_map.get(callback.data, "не указано")
        user_data[uid]["diamonds"] += 1
        logging.info(f"income_need: брильянты для {uid} = {user_data[uid]['diamonds']}")
        
        # Брильянт
        await asyncio.sleep(0.7)
        await callback.message.answer("\n\n\n          💎\n\n\n")
        
        await asyncio.sleep(1)
        motivational_msg = await callback.message.answer(
            "Отличный выбор! Теперь последний шаг 👇"
        )
        
        await asyncio.sleep(3)
        await motivational_msg.delete()
        
        # Финал блока - предложение подписаться с переходом в канал
        total = user_data[uid]["diamonds"]
        logging.info(f"income_need: показ блока подписки для {uid}, брильянтов: {total}")
        
        # Показываем URL-кнопку для подписки на канал
        kb = InlineKeyboardBuilder()
        if CHANNEL_URL:
            kb.button(text="🔔 Подписаться на канал", url=CHANNEL_URL)
            kb.adjust(1)
            button_text = "👇 Нажми на кнопку ниже, чтобы подписаться:"
            logging.info(f"income_need: отправка сообщения с кнопкой подписки для {uid}, URL: {CHANNEL_URL}")
        else:
            logging.error(f"income_need: CHANNEL_URL не установлен для пользователя {uid}")
            button_text = ""
        
        msg = await callback.message.answer(
            f"💎 Отлично! Ты прошёл блок карьерного развития.\n"
            f"У тебя сейчас {total} брильянтов 🌟\n\n"
            "🔔 Подпишись на наш канал!\n"
            "💎 После подписки общее количество брильянтов будет равно 19!\n\n"
            f"{button_text}",
            reply_markup=kb.as_markup() if CHANNEL_URL else None
        )
        await callback.answer()
        await state.clear()
        logging.info(f"income_need: сообщение с кнопкой подписки отправлено для {uid}, состояние очищено")
        
        # Ждем 6 секунд и автоматически показываем кнопку ПРОДОЛЖИТЬ
        logging.info(f"income_need: ожидание 6 секунд перед показом кнопки ПРОДОЛЖИТЬ для {uid}")
        await asyncio.sleep(6)
        
        kb2 = InlineKeyboardBuilder()
        kb2.button(text="✅ ПРОДОЛЖИТЬ ✅", callback_data="inc_sub")
        kb2.adjust(1)
        
        logging.info(f"income_need: отправка кнопки ПРОДОЛЖИТЬ для {uid}")
        await callback.message.answer(
            "✅ После подписки нажми ПРОДОЛЖИТЬ:",
            reply_markup=kb2.as_markup()
        )
        logging.info(f"income_need: кнопка ПРОДОЛЖИТЬ отправлена для {uid}")
    except Exception as e:
        logging.error(f"Ошибка в income_need: {e}")
        await callback.answer("Произошла ошибка, попробуйте позже", show_alert=True)

# Обработчик пола после возраста (inc_gender_after_age) уже создан выше
# Старый обработчик inc_gender удален, так как пол теперь спрашивается после возраста

@dp.callback_query(F.data == "inc_sub")
async def income_sub(callback: CallbackQuery):
    uid = callback.from_user.id
    logging.info(f"income_sub: вызван для пользователя {uid}")
    
    # Проверяем подписку на канал
    logging.info(f"income_sub: проверка подписки для {uid}")
    is_subscribed = await check_subscription(uid)
    logging.info(f"income_sub: результат проверки подписки для {uid} = {is_subscribed}")
    
    if not is_subscribed:
        # Если не подписан - показываем предупреждение
        await callback.answer(
            "⚠️ Сначала подпишись на канал!",
            show_alert=True
        )
        
        # Дополнительное сообщение с напоминанием
        kb = InlineKeyboardBuilder()
        if not CHANNEL_URL:
            logging.error(f"income_sub: CHANNEL_URL не установлен для пользователя {uid}")
            channel_text = "Пожалуйста, подпишись на канал!\n\n"
        else:
            kb.button(text="🔔 Подписаться на канал", url=CHANNEL_URL)
            channel_text = f"Пожалуйста, подпишись на канал:\n{CHANNEL_URL}\n\n"
        kb.button(text="━━━━━━━━  ✅ ПРОДОЛЖИТЬ ✅  ━━━━━━━━", callback_data="inc_sub")
        kb.adjust(1)
        
        await callback.message.answer(
            "❌ Подписка не обнаружена!\n\n"
            f"{channel_text}"
            "После подписки нажми кнопку 'ПРОДОЛЖИТЬ' снова",
            reply_markup=kb.as_markup()
        )
        return
    
    # Если подписан - продолжаем
    # В ветке "Хочу доход" добавляем 6 брильянтов (13 вопросов + 6 = 19)
    user_data[uid]["diamonds"] = clamp_points(user_data[uid]["diamonds"] + 6)
    
    send_to_amocrm(uid)
    
    # 1. Анимационное конфетти
    try:
        confetti_boom = "CAACAgIAAxkBAAICW2Z-xQjOqTx9AAE3QfEHj6wVNf3YNQACMhYAAlQ_6Eu9D4QAAYvQoiw0BA"
        await callback.message.answer_sticker(sticker=confetti_boom)
    except:
        await callback.message.answer("🎊")
    
    await asyncio.sleep(1.5)
    
    # 2. Анимационный кубок
    try:
        trophy_sticker = "CAACAgIAAxkBAAICXGZ-xRJkf0OQdHLGb_xQJXhXYKSVAAIkFgACVD_oS1zZnwAB-FS51jQE"
        await callback.message.answer_sticker(sticker=trophy_sticker)
    except:
        await callback.message.answer("🏆")
    
    await asyncio.sleep(1.5)
    
    # 3. Первое сообщение: Вы выиграли + баланс
    total_diamonds = user_data[uid]['diamonds']
    await callback.message.answer(
        f"🎉 ВЫ ВЫИГРАЛИ! 🎉\n\n"
        f"💎 У вас {total_diamonds} брильянтов 💎"
    )
    
    await asyncio.sleep(2)
    
    # 4. Второе сообщение с призывом пригласить друга (показывается 6 секунд)
    invite_msg = await callback.message.answer(
        "🎁 Подарок уже почти твой!\n\n"
        "> Для него тебе нужен всего один бриллиант 💎\n\n"
        "👥 Просто пригласи одного друга в путешествие Coral Quest —\n"
        "> и получи свой заслуженный приз вместе с новыми впечатлениями! 🌟"
    )
    
    await asyncio.sleep(6)
    
    # 5. Удаляем предыдущее сообщение
    await invite_msg.delete()
    
    # 6. Анимационная рука показывает вниз
    await callback.message.answer("👇")
    
    await asyncio.sleep(1)
    
    # 7. Первые кнопки: Пригласить друга и Баланс
    kb = InlineKeyboardBuilder()
    kb.button(text="👥 Пригласить друга", callback_data="invite")
    kb.button(text="💰 Мой баланс", callback_data="balance")
    kb.adjust(1)
    
    await callback.message.answer(
        "👇 Выбери действие:",
        reply_markup=kb.as_markup()
    )
    
    await callback.answer()

# ===========================================================
# Общие команды меню
# ===========================================================
@dp.callback_query(F.data == "invite")
async def invite(callback: CallbackQuery):
    uid = callback.from_user.id
    logging.info(f"invite: вызван для пользователя {uid}")
    ref_link = user_data[uid]["ref_link"]
    logging.info(f"invite: реферальная ссылка для {uid} = {ref_link}")
    
    # Начисляем 1 брильянт сразу при отправке ссылки
    if uid not in user_data:
        user_data[uid] = {"diamonds": 0}
    before = user_data[uid].get("diamonds", 0)
    user_data[uid]["diamonds"] = clamp_points(user_data[uid].get("diamonds", 0) + 1)
    after = user_data[uid]["diamonds"]
    logging.info(f"invite: начислен 1 брильянт пользователю {uid} (было {before}, стало {after})")
    
    logging.info(f"invite: отправка реферальной ссылки для {uid}")
    await callback.message.answer(
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"   🔗 Твоя реферальная ссылка:\n\n"
        f"   {ref_link}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "   📤 Отправь эту ссылку другу\n"
        "   💎 +1 брильянт за отправку ссылки!"
    )
    
    await asyncio.sleep(1)
    
    # Показываем кнопку "Забрать приз"
    logging.info(f"invite: создание кнопки ЗАБРАТЬ ПРИЗ для {uid}")
    kb_prize = InlineKeyboardBuilder()
    kb_prize.button(text="🎁 ЗАБРАТЬ ПРИЗ", callback_data="get_prize")
    kb_prize.adjust(1)
    
    logging.info(f"invite: отправка кнопки ЗАБРАТЬ ПРИЗ для {uid}")
    await callback.message.answer(
        "👇 Выбери действие:",
        reply_markup=kb_prize.as_markup()
    )
    logging.info(f"invite: кнопка ЗАБРАТЬ ПРИЗ отправлена для {uid}")
    
    await callback.answer()

# Обработчик кнопки "Забрать приз"
@dp.callback_query(F.data == "get_prize")
async def get_prize(callback: CallbackQuery):
    try:
        uid = callback.from_user.id
        logging.info(f"get_prize вызван для пользователя {uid}")
        
        # ID канала для отправки данных
        REPORT_CHANNEL_ID = -1003317524713
        
        # Словари для перевода технических значений в русский текст
        branch_names = {
            'health': 'Здоровье',
            'income': 'Доход'
        }
        
        goal_names = {
            'h_goal_energy': 'Энергия',
            'h_goal_immune': 'Иммунитет',
            'h_goal_sleep': 'Сон',
            'h_goal_fit': 'Похудение'
        }
        
        water_names = {
            'water_1': '1 литр',
            'water_1_5': '1.5 литра',
            'water_2': '2 литра',
            'water_3': '3+ литра'
        }
        
        food_names = {
            'food_meat': 'Мясо',
            'food_fish': 'Рыбу',
            'food_sushi': 'Суши',
            'food_veg': 'Вегетарианец'
        }
        
        freq_names = {
            'eat_day': 'Каждый день',
            'eat_week': 'Раз в неделю',
            'eat_month': 'Раз в месяц',
            'eat_never': 'Почти не ем'
        }
        
        veg_names = {
            'veg_daily': 'Каждый день',
            'veg_sometimes': 'Иногда',
            'veg_rare': 'Редко',
            'veg_no': 'Не ем'
        }
        
        green_names = {
            'green_daily': 'Каждый день',
            'green_sometimes': 'Иногда',
            'green_rare': 'Редко',
            'green_no': 'Нет'
        }
        
        drink_names = {
            'drink_coffee': 'Кофе',
            'drink_tea': 'Чай',
            'drink_no': 'Не пью',
            'drink_other': 'Другое'
        }
        
        drink_freq_names = {
            'daily': 'Каждый день',
            'weekly': 'Раз в неделю',
            'monthly': 'Раз в месяц',
            'never': 'Почти не пью'
        }
        
        vitamins_names = {
            'vitamins_regular': 'Да, регулярно',
            'vitamins_sometimes': 'Иногда',
            'vitamins_rare': 'Редко',
            'vitamins_never': 'Никогда'
        }
        
        # Формируем отчет с ответами пользователя
        user_info = user_data.get(uid, {})
        logging.info(f"get_prize: user_info для {uid} = {user_info}")
        answers = user_info.get("answers", {})
        logging.info(f"get_prize: answers для {uid} = {answers}")
        
        # Переводим значения
        branch = branch_names.get(user_info.get('branch', ''), 'Не указано')
        logging.info(f"get_prize: branch для {uid} = {branch}")
        goal = goal_names.get(answers.get('goal', ''), 'Не указано')
        water = water_names.get(answers.get('water', ''), 'Не указано')
        food = food_names.get(answers.get('food', ''), 'Не указано')
        
        # Частота еды может содержать префикс, поэтому ищем по концовке
        eat_freq = answers.get('eat_freq', '')
        eat_freq_text = 'Не указано'
        if 'day' in eat_freq:
            eat_freq_text = 'Каждый день'
        elif 'week' in eat_freq:
            eat_freq_text = 'Раз в неделю'
        elif 'month' in eat_freq:
            eat_freq_text = 'Раз в месяц'
        elif 'never' in eat_freq:
            eat_freq_text = 'Почти не ем'
        
        vegetables = veg_names.get(answers.get('vegetables', ''), 'Не указано')
        greens = green_names.get(answers.get('greens', ''), 'Не указано')
        drink = drink_names.get(answers.get('drink', ''), 'Не указано')
        
        # Частота напитков
        drink_freq = answers.get('drink_freq', '')
        drink_freq_text = 'Не указано'
        if 'day' in drink_freq:
            drink_freq_text = 'Каждый день'
        elif 'week' in drink_freq:
            drink_freq_text = 'Раз в неделю'
        elif 'month' in drink_freq:
            drink_freq_text = 'Раз в месяц'
        elif 'never' in drink_freq:
            drink_freq_text = 'Почти не пью'
        
        vitamins = vitamins_names.get(answers.get('vitamins', ''), 'Не указано')
        
        # Проверяем ветку и формируем отчет соответственно
        if user_info.get('branch') == 'health':
            report = f"""
📊 НОВАЯ ЗАЯВКА НА ПРИЗ

👤 Пользователь:
├ Telegram ID: {uid}
├ Username: @{callback.from_user.username or 'не указан'}
├ Имя: {user_info.get('name', 'не указано')}

📝 ОТВЕТЫ НА ВОПРОСЫ:

🏥 Ветка: {branch}

📋 Личные данные:
├ Возраст: {answers.get('age', 'не указано')} лет
├ Рост: {answers.get('height', 'не указано')} см
├ Вес: {answers.get('weight', 'не указано')} кг
├ Пол: {user_info.get('gender', 'не указано')}

🎯 Цель: {goal}

🍽 Питание:
├ Вода в день: {water}
├ Что чаще ест: {food}
├ Как часто: {eat_freq_text}
├ Овощи: {vegetables}
├ Зелень: {greens}

☕ Напитки и добавки:
├ Кофе/Чай: {drink}
├ Как часто пьет: {drink_freq_text}
├ Витамины/БАДы: {vitamins}

💎 Брильянты: {user_info.get('diamonds', 0)}

🔗 Реферальная ссылка: {user_info.get('ref_link', 'не указано')}
"""
        else:  # income
            report = f"""
📊 НОВАЯ ЗАЯВКА НА ПРИЗ

👤 Пользователь:
├ Telegram ID: {uid}
├ Username: @{callback.from_user.username or 'не указан'}
├ Имя: {user_info.get('name', 'не указано')}

📝 ОТВЕТЫ НА ВОПРОСЫ:

💼 Ветка: {branch}

📋 Личные данные:
├ Возраст: {answers.get('age', 'не указано')} лет
├ Пол: {user_info.get('gender', 'не указано')}

💰 Карьерные цели:
├ Желаемый доход: {answers.get('desired_income', 'не указано')}
├ Формат работы: {answers.get('work_format', 'не указано')}
├ Стиль работы: {answers.get('work_style', 'не указано')}

📊 Опыт и развитие:
├ Опыт: {answers.get('experience', 'не указано')}
├ Сфера: {answers.get('sphere', 'не указано')}
├ Навыки для развития: {answers.get('skills', 'не указано')}

⏰ Готовность и ценности:
├ Время в день: {answers.get('time_invest', 'не указано')}
├ Ценности в работе: {answers.get('values', 'не указано')}
├ Готовность начать: {answers.get('ready_start', 'не указано')}
├ Что нужно: {answers.get('need_start', 'не указано')}

💎 Брильянты: {user_info.get('diamonds', 0)}

🔗 Реферальная ссылка: {user_info.get('ref_link', 'не указано')}
"""
        
        logging.info(f"get_prize: отчет сформирован для {uid}, длина отчета: {len(report)} символов")
        
        # Отправляем отчет в канал
        try:
            logging.info(f"get_prize: отправка отчета в канал {REPORT_CHANNEL_ID} для {uid}")
            await bot.send_message(REPORT_CHANNEL_ID, report)
            logging.info(f"get_prize: отчет успешно отправлен в канал для {uid}")
        except Exception as e:
            logging.error(f"get_prize: ошибка отправки в канал для {uid}: {e}", exc_info=True)
        
        # Показываем пользователю ссылку на приз
        gender = user_info.get("gender", "Женщина")
        logging.info(f"get_prize: пол пользователя {uid} = {gender}")
        
        # Определяем ссылку в зависимости от пола
        if gender == "Женщина":
            # Для женщин: используем REF_LINK_WOMAN или fallback на https://coral.club/8559063.html
            ref_link_coral = REF_LINK_WOMAN or "https://coral.club/8559063.html"
        else:
            # Для мужчин: используем REF_LINK_MAN или fallback на https://coral.club/8701238.html
            ref_link_coral = REF_LINK_MAN or "https://coral.club/8701238.html"
        
        if not REF_LINK_WOMAN and gender == "Женщина":
            logging.warning(f"get_prize: REF_LINK_WOMAN не установлен, используется fallback для {uid}")
        elif not REF_LINK_MAN and gender != "Женщина":
            logging.warning(f"get_prize: REF_LINK_MAN не установлен, используется fallback для {uid}")
        
        logging.info(f"get_prize: ссылка на приз для {uid} = {ref_link_coral}")
        
        kb_prize = InlineKeyboardBuilder()
        if ref_link_coral:
            kb_prize.button(text="🎁 Перейти за призом", url=ref_link_coral)
            kb_prize.adjust(1)
        else:
            logging.error(f"get_prize: невозможно создать кнопку, ссылка не установлена для {uid}")
        
        logging.info(f"get_prize: отправка сообщения пользователю {uid} с кнопкой приза")
        await callback.message.answer(
            "🎉 Отлично! Твои данные отправлены.\n"
            "👇 Нажми на кнопку ниже, чтобы забрать свой приз:",
            reply_markup=kb_prize.as_markup() if ref_link_coral else None
        )
        logging.info(f"get_prize: сообщение с кнопкой успешно отправлено пользователю {uid}")
        
        await callback.answer()
        logging.info(f"get_prize успешно завершен для пользователя {uid}")
    except Exception as e:
        logging.error(f"get_prize: КРИТИЧЕСКАЯ ОШИБКА для пользователя {uid}: {e}", exc_info=True)
        logging.error(f"get_prize: тип ошибки: {type(e).__name__}")
        logging.error(f"get_prize: traceback: {e.__traceback__}")
        try:
            await callback.answer("Произошла ошибка, попробуйте позже", show_alert=True)
        except Exception as e2:
            logging.error(f"get_prize: ошибка при отправке alert для {uid}: {e2}")

@dp.callback_query(F.data == "balance")
async def balance(callback: CallbackQuery):
    uid = callback.from_user.id
    diamonds = user_data.get(uid, {}).get("diamonds", 0)
    await callback.answer(f"💰 У тебя {diamonds} брильянтов", show_alert=True)

@dp.callback_query(F.data == "consultant")
async def consultant(callback: CallbackQuery):
    await callback.message.answer(f"📞 Связаться с менеджером: {CONSULTANT_LINK}")
    await callback.answer()

# ===========================================================
# ЗАПУСК
# ===========================================================
async def main():
    print("✅ Бот запущен! Нажмите Ctrl+C для остановки.")
    # Сбрасываем webhook и ожидающие обновления перед запуском
    try:
        # Очистка webhook (одна попытка)
        try:
            await bot.delete_webhook(drop_pending_updates=True)
            logging.info("Webhook очищен")
        except Exception as e:
            logging.warning(f"Ошибка очистки webhook: {e}")
    except Exception as e:
        logging.warning(f"Ошибка при подготовке: {e}")
    
    logging.info("Запуск polling...")
    await dp.start_polling(bot, drop_pending_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
