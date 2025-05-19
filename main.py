import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

API_TOKEN = "8017145191:AAGSYBmDdAVr1y4_Otk41jjJuRprZJKc8ls"
MAIN_ADMIN_ID = 7828532363

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

admins = {MAIN_ADMIN_ID}
banned_users = set()
authorized_admins = set()
user_context = {}
user_in_support = set()

admin_password = "qwerty123"  # Пароль для авторизации


class ReplyState(StatesGroup):
    waiting_for_reply = State()


# --- Кнопки ---
main_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Дүкен", callback_data="shop")],
    [InlineKeyboardButton(text="Әлеуметтік желілер", callback_data="socials")],
    [InlineKeyboardButton(text="Тех. Поддержка", callback_data="support")]
])

admin_panel = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Пользователи в поддержке", callback_data="show_support_users")],
    [InlineKeyboardButton(text="Список админов", callback_data="list_admins")],
])


@dp.message(Command("start"))
async def cmd_start(message: Message):
    if message.from_user.id in banned_users:
        return
    await message.answer("Сәлем! Мен — Көмекші Томпақ. Не қажет?", reply_markup=main_menu)


@dp.callback_query(F.data == "shop")
async def shop_handler(callback: CallbackQuery):
    await callback.message.answer("GOLD KAZAKHSTAN донат дүкені:\nhttps://example.com")
    await callback.answer()


@dp.callback_query(F.data == "socials")
async def socials_handler(callback: CallbackQuery):
    await callback.message.answer(
        "Форум: https://forum.kz\n"
        "Сайт: https://site.kz\n"
        "Канал: https://t.me/channel"
    )
    await callback.answer()


@dp.callback_query(F.data == "support")
async def support_handler(callback: CallbackQuery):
    user_in_support.add(callback.from_user.id)
    await callback.message.answer("Сұрағыңызды жазыңыз. Админге жіберіледі.")
    await callback.answer()


@dp.message()
async def handle_user_message(message: Message):
    uid = message.from_user.id
    if uid in admins:
        return
    if uid in banned_users:
        return
    if uid not in user_in_support:
        return await message.answer("Сәлем! Алдымен 'Тех. Поддержка' батырмасын басыңыз.")

    text = (
        f"<b>[ТЕХ. ҚОЛДАУ]</b>\n"
        f"<b>Аты:</b> {message.from_user.full_name}\n"
        f"<b>Username:</b> @{message.from_user.username or 'жоқ'}\n"
        f"<b>User ID:</b> {uid}\n\n"
        f"{message.text}"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✉️ Жауап беру", callback_data=f"reply:{uid}")],
        [InlineKeyboardButton(
            text=("❌ Снять админку" if uid in admins else "✅ Беру админку"),
            callback_data=f"toggleadmin:{uid}")],
        [InlineKeyboardButton(
            text=("♻️ Разбан" if uid in banned_users else "⛔ Бан"),
            callback_data=f"toggleban:{uid}")]
    ])

    for admin_id in admins:
        await bot.send_message(admin_id, text, reply_markup=keyboard)

    await message.answer("Хабарлама техникалық қолдау тобына жіберілді.")
    user_in_support.discard(uid)


@dp.callback_query(F.data.startswith("reply:"))
async def start_reply(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in authorized_admins:
        return await callback.answer("Рұқсат жоқ", show_alert=True)

    target_id = int(callback.data.split(":")[1])
    user_context[callback.from_user.id] = target_id
    await state.set_state(ReplyState.waiting_for_reply)
    await callback.message.answer(f"✍️ Жауап жаз (ID: {target_id}):")
    await callback.answer()


@dp.message(ReplyState.waiting_for_reply)
async def send_reply(message: Message, state: FSMContext):
    target_id = user_context.get(message.from_user.id)
    if not target_id:
        await message.answer("Қате: қолданушы табылмады.")
        return await state.clear()

    try:
        await bot.send_message(target_id, f"<b>Админ:</b>\n\n{message.text}")
        await message.answer("✅ Жіберілді.")
    except:
        await message.answer("❌ Жіберілмеді.")

    await state.clear()
    user_context.pop(message.from_user.id, None)


@dp.callback_query(F.data.startswith("toggleadmin:"))
async def toggle_admin(callback: CallbackQuery):
    if callback.from_user.id != MAIN_ADMIN_ID:
        return await callback.answer("Рұқсат жоқ", show_alert=True)

    uid = int(callback.data.split(":")[1])
    if uid == MAIN_ADMIN_ID:
        return await callback.answer("Басты админді өзгертуге болмайды.")

    if uid in admins:
        admins.remove(uid)
        await callback.message.answer(f"❌ {uid} админ емес.")
    else:
        admins.add(uid)
        await callback.message.answer(f"✅ {uid} енді админ.")
    await callback.answer()


@dp.callback_query(F.data.startswith("toggleban:"))
async def toggle_ban(callback: CallbackQuery):
    if callback.from_user.id not in authorized_admins:
        return await callback.answer("Рұқсат жоқ", show_alert=True)

    uid = int(callback.data.split(":")[1])
    if uid in banned_users:
        banned_users.remove(uid)
        await callback.message.answer(f"♻️ {uid} енді разбан.")
    else:
        banned_users.add(uid)
        await callback.message.answer(f"⛔ {uid} банға түсті.")
    await callback.answer()


# --- Авторизация через пароль ---
@dp.message(Command("adminlogin"))
async def login_admin(message: Message):
    args = message.text.split()
    if len(args) != 2:
        return await message.answer("Қолданылуы: /adminlogin [пароль]")

    if message.from_user.id not in admins:
        return await message.answer("Сіз жалпы админ емессіз.")

    if args[1] == admin_password:
        authorized_admins.add(message.from_user.id)
        await message.answer("✅ Авторизация сәтті өтті. /admin теріңіз.")
    else:
        await message.answer("❌ Қате пароль.")


# --- Админ-панель ---
@dp.message(Command("admin"))
async def admin_panel_handler(message: Message):
    if message.from_user.id not in authorized_admins:
        return await message.answer("Сіз авторизациядан өтпегенсіз. /adminlogin [пароль] теріңіз.")
    await message.answer("Админ панелі:", reply_markup=admin_panel)


@dp.callback_query(F.data == "show_support_users")
async def show_support_users(callback: CallbackQuery):
    if callback.from_user.id not in authorized_admins:
        return await callback.answer("Рұқсат жоқ", show_alert=True)

    if not user_in_support:
        await callback.message.answer("Қолдау сұрағандар жоқ.")
    else:
        users = "\n".join([str(uid) for uid in user_in_support])
        await callback.message.answer(f"Қолдау сұрағандар:\n{users}")
    await callback.answer()


@dp.callback_query(F.data == "list_admins")
async def list_admins(callback: CallbackQuery):
    if callback.from_user.id not in authorized_admins:
        return await callback.answer("Рұқсат жоқ", show_alert=True)

    text = "<b>Админдер тізімі:</b>\n" + "\n".join(str(admin_id) for admin_id in admins)
    await callback.message.answer(text)
    await callback.answer()


# --- Ручное добавление/удаление админов ---
@dp.message(Command("setadmin"))
async def setadmin_cmd(message: Message):
    if message.from_user.id != MAIN_ADMIN_ID:
        return await message.answer("Сізде рұқсат жоқ.")

    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        return await message.answer("Қолданылуы: /setadmin [user_id]")

    new_admin = int(args[1])
    admins.add(new_admin)
    await message.answer(f"✅ {new_admin} енді админ.")


@dp.message(Command("removeadmin"))
async def removeadmin_cmd(message: Message):
    if message.from_user.id != MAIN_ADMIN_ID:
        return await message.answer("Сізде рұқсат жоқ.")

    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        return await message.answer("Қолданылуы: /removeadmin [user_id]")

    rem_admin = int(args[1])
    if rem_admin == MAIN_ADMIN_ID:
        return await message.answer("Басты админді өшіруге болмайды.")
    admins.discard(rem_admin)
    await message.answer(f"❌ {rem_admin} енді админ емес.")


# --- Запуск ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())