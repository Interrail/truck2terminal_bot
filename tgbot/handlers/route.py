import asyncio

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram3_calendar import SimpleCalendar, simple_cal_callback

from infrastructure.some_api.api import MyApi
from tgbot.handlers.cancel import CANCEL_TRANSLATIONS
from tgbot.services.auto_cancel import auto_cancel_after_timeout
from tgbot.services.location_validation import validate_driver_location

route_router = Router()


class RouteCreationStates(StatesGroup):
    waiting_for_terminal = State()
    waiting_for_eta_date = State()
    waiting_for_eta_hour = State()
    waiting_for_container_name = State()
    waiting_for_container_size = State()
    waiting_for_container_type = State()


ROUTE_CREATION_TRANSLATIONS = {
    "uz": {
        "select_terminal": "🏢 Terminalni tanlang (1/6):",
        "select_eta_date": "📅 Yetib kelish sanasini tanlang (2/6):",
        "select_eta_hour": "🕒 Yetib kelish soatini tanlang (3/6):",
        "enter_container_name": "📦 Konteyner nomini kiriting (4/6):\nMisol: ABCD1234567",
        "select_container_size": "📏 Konteyner o'lchamini tanlang (5/6):",
        "select_container_type": "🔍 Konteyner turini tanlang (6/6):",
        "summary": "📋 Sizning marshrutingiz:",
        "truck": "🚛 Yuk mashinasi:",
        "terminal": "🏢 Terminal:",
        "eta": "📅 Yetib kelish vaqti:",
        "container": "📦 Konteyner:",
        "size": "📏 O'lcham:",
        "type": "🔍 Tip:",
        "creating_route": "✅ Ma'lumotlar tasdiqlandi. Yo'nalish yaratilmoqda...",
        "live_location": "✅ Yo'nalish yaratildi!\n\n🚛 Iltimos, 📎 tugmasini bosib, Joylashuv → Jonli joylashuv ulashing.",
        "cancel": "❌ Bekor qilish",
        "loaded": "Yuklangan 📦",
        "empty": "Bo'sh 📭",
    },
    "ru": {
        "select_terminal": "🏢 Выберите терминал (1/6):",
        "select_eta_date": "📅 Выберите дату прибытия (2/6):",
        "select_eta_hour": "🕒 Выберите час прибытия (3/6):",
        "enter_container_name": "📦 Введите название контейнера (4/6):\nПример: ABCD1234567",
        "select_container_size": "📏 Выберите размер контейнера (5/6):",
        "select_container_type": "🔍 Выберите тип контейнера (6/6):",
        "summary": "📋 Ваш маршрут:",
        "truck": "🚛 Машина:",
        "terminal": "🏢 Терминал:",
        "eta": "📅 Время прибытия:",
        "container": "📦 Контейнер:",
        "size": "📏 Размер:",
        "type": "🔍 Тип:",
        "creating_route": "✅ Данные подтверждены. Создание маршрута...",
        "live_location": "✅ Маршрут успешно создан!\n\n🚛 Пожалуйста, нажмите 📎 → Местоположение → Поделиться живым местоположением.",
        "cancel": "❌ Отмена",
        "loaded": "Загруженный 📦",
        "empty": "Пустой 📭",
    },
}


async def build_summary(state: FSMContext, language: str) -> str:
    data = await state.get_data()
    lines = [ROUTE_CREATION_TRANSLATIONS[language]["summary"]]

    if truck := data.get("truck_number"):
        lines.append(f"{ROUTE_CREATION_TRANSLATIONS[language]['truck']} {truck}")
    if terminal := data.get("selected_terminal_name"):
        lines.append(f"{ROUTE_CREATION_TRANSLATIONS[language]['terminal']} {terminal}")
    if eta_date := data.get("eta_date"):
        if eta_hour := data.get("eta_hour"):
            lines.append(
                f"{ROUTE_CREATION_TRANSLATIONS[language]['eta']} {eta_date} {eta_hour}:00"
            )
    if container := data.get("container_name"):
        lines.append(
            f"{ROUTE_CREATION_TRANSLATIONS[language]['container']} {container}"
        )
    if size := data.get("container_size"):
        lines.append(f"{ROUTE_CREATION_TRANSLATIONS[language]['size']} {size} ft")
    if cont_type := data.get("container_type"):
        lines.append(f"{ROUTE_CREATION_TRANSLATIONS[language]['type']} {cont_type}")

    return "\n".join(lines)


@route_router.message(F.text.in_(["➕ Yo'nalish qo'shish", "➕ Добавить маршрут"]))
async def start_route_creation(
    message: Message,
    state: FSMContext,
    truck_number: str,
    language: str,
    api_client: MyApi,
):
    await state.clear()
    api = api_client or MyApi()

    if not truck_number:
        await message.answer("❌ No truck number found. Update your profile first.")
        return

    # ✅ Validate Live Location BEFORE starting Route FSM
    is_valid = await validate_driver_location(message, message.from_user.id, api)

    if not is_valid:
        return  # ❌ Stop if location not valid

    language = language or "uz"
    await state.update_data(truck_number=truck_number, language=language)

    terminals = await api.get_terminals(telegram_id=message.from_user.id)
    if not terminals:
        await message.answer("❌ No terminals found.")
        return

    terminals_dict = {t["name"]: t["id"] for t in terminals}
    await state.update_data(terminals=terminals_dict)

    builder = InlineKeyboardBuilder()
    for name in terminals_dict.keys():
        builder.button(text=name, callback_data=name)
    builder.adjust(1)
    builder.row(
        InlineKeyboardBuilder()
        .button(
            text=ROUTE_CREATION_TRANSLATIONS[language]["cancel"],
            callback_data="cancel_route",
        )
        .as_markup()
        .inline_keyboard[0][0]
    )

    summary = await build_summary(state, language)
    await message.answer(
        f"{summary}\n\n{ROUTE_CREATION_TRANSLATIONS[language]['select_terminal']}",
        reply_markup=builder.as_markup(),
    )
    await state.set_state(RouteCreationStates.waiting_for_terminal)
    asyncio.create_task(auto_cancel_after_timeout(message, state))


@route_router.callback_query(RouteCreationStates.waiting_for_terminal)
async def terminal_selected(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    data = await state.get_data()
    terminals = data.get("terminals", {})
    language = data.get("language", "uz")

    if callback.data == "cancel_route":
        await state.clear()
        await callback.message.answer(CANCEL_TRANSLATIONS[language]["process_canceled"])
        return

    terminal_name = callback.data
    if terminal_name not in terminals:
        await callback.message.answer("⚠️ Please select from buttons.")
        return

    await state.update_data(
        selected_terminal_id=terminals[terminal_name],
        selected_terminal_name=terminal_name,
    )

    summary = await build_summary(state, language)
    calendar = SimpleCalendar()

    calendar_markup = await calendar.start_calendar()
    builder = InlineKeyboardBuilder()
    for row in calendar_markup.inline_keyboard:
        builder.row(*row)
    builder.row(
        InlineKeyboardBuilder()
        .button(
            text=ROUTE_CREATION_TRANSLATIONS[language]["cancel"],
            callback_data="cancel_route",
        )
        .as_markup()
        .inline_keyboard[0][0]
    )

    await callback.message.edit_text(
        f"{summary}\n\n{ROUTE_CREATION_TRANSLATIONS[language]['select_eta_date']}",
        reply_markup=builder.as_markup(),
    )
    await state.set_state(RouteCreationStates.waiting_for_eta_date)
    asyncio.create_task(auto_cancel_after_timeout(callback.message, state))


@route_router.callback_query(
    RouteCreationStates.waiting_for_eta_date, simple_cal_callback.filter()
)
async def eta_date_selected(
    callback: CallbackQuery, callback_data: dict, state: FSMContext
):
    selected, date = await SimpleCalendar().process_selection(callback, callback_data)
    if selected:
        await state.update_data(eta_date=date.strftime("%Y-%m-%d"))
        await state.set_state(RouteCreationStates.waiting_for_eta_hour)

        data = await state.get_data()
        language = data.get("language", "uz")

        summary = await build_summary(state, language)
        builder = InlineKeyboardBuilder()
        for hour in range(7, 20):
            builder.button(text=f"{hour}:00", callback_data=f"hour_{hour}")
        builder.adjust(4)
        builder.row(
            InlineKeyboardBuilder()
            .button(
                text=ROUTE_CREATION_TRANSLATIONS[language]["cancel"],
                callback_data="cancel_route",
            )
            .as_markup()
            .inline_keyboard[0][0]
        )

        await callback.message.edit_text(
            f"{summary}\n\n{ROUTE_CREATION_TRANSLATIONS[language]['select_eta_hour']}",
            reply_markup=builder.as_markup(),
        )
        asyncio.create_task(auto_cancel_after_timeout(callback.message, state))


@route_router.callback_query(
    RouteCreationStates.waiting_for_eta_hour, F.data.startswith("hour_")
)
async def eta_hour_selected(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    if callback.data == "cancel_route":
        data = await state.get_data()
        language = data.get("language", "uz")
        await state.clear()
        await callback.message.answer(CANCEL_TRANSLATIONS[language]["process_canceled"])
        return

    hour = callback.data.split("_")[1]
    await state.update_data(eta_hour=hour)

    data = await state.get_data()
    language = data.get("language", "uz")

    summary = await build_summary(state, language)
    await state.set_state(RouteCreationStates.waiting_for_container_name)

    cancel_instruction = (
        f"\n\n{ROUTE_CREATION_TRANSLATIONS[language]['cancel']}: /cancel"
    )

    await callback.message.edit_text(
        f"{summary}\n\n{ROUTE_CREATION_TRANSLATIONS[language]['enter_container_name']}{cancel_instruction}"
    )
    asyncio.create_task(auto_cancel_after_timeout(callback.message, state))


@route_router.message(RouteCreationStates.waiting_for_container_name)
async def container_name_received(message: Message, state: FSMContext):
    if message.text.lower() in ["/cancel", "cancel"]:
        data = await state.get_data()
        language = data.get("language", "uz")
        await state.clear()
        await message.answer(CANCEL_TRANSLATIONS[language]["process_canceled"])
        return

    await state.update_data(container_name=message.text.strip())
    data = await state.get_data()
    language = data.get("language", "uz")

    summary = await build_summary(state, language)

    builder = InlineKeyboardBuilder()
    for size in ["20", "40", "45"]:
        builder.button(text=f"{size} ft", callback_data=f"size_{size}")
    builder.adjust(3)
    builder.row(
        InlineKeyboardBuilder()
        .button(
            text=ROUTE_CREATION_TRANSLATIONS[language]["cancel"],
            callback_data="cancel_route",
        )
        .as_markup()
        .inline_keyboard[0][0]
    )

    await message.answer(
        f"{summary}\n\n{ROUTE_CREATION_TRANSLATIONS[language]['select_container_size']}",
        reply_markup=builder.as_markup(),
    )
    await state.set_state(RouteCreationStates.waiting_for_container_size)
    asyncio.create_task(auto_cancel_after_timeout(message, state))


@route_router.callback_query(
    RouteCreationStates.waiting_for_container_size, F.data.startswith("size_")
)
async def container_size_selected(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    if callback.data == "cancel_route":
        data = await state.get_data()
        language = data.get("language", "uz")
        await state.clear()
        await callback.message.answer(CANCEL_TRANSLATIONS[language]["process_canceled"])
        return

    size = callback.data.split("_")[1]
    await state.update_data(container_size=size)

    data = await state.get_data()
    language = data.get("language", "uz")

    summary = await build_summary(state, language)

    builder = InlineKeyboardBuilder()
    builder.button(
        text=ROUTE_CREATION_TRANSLATIONS[language]["loaded"], callback_data="laden"
    )
    builder.button(
        text=ROUTE_CREATION_TRANSLATIONS[language]["empty"], callback_data="empty"
    )
    builder.adjust(2)
    builder.row(
        InlineKeyboardBuilder()
        .button(
            text=ROUTE_CREATION_TRANSLATIONS[language]["cancel"],
            callback_data="cancel_route",
        )
        .as_markup()
        .inline_keyboard[0][0]
    )

    await callback.message.edit_text(
        f"{summary}\n\n{ROUTE_CREATION_TRANSLATIONS[language]['select_container_type']}",
        reply_markup=builder.as_markup(),
    )
    await state.set_state(RouteCreationStates.waiting_for_container_type)
    asyncio.create_task(auto_cancel_after_timeout(callback.message, state))


@route_router.callback_query(RouteCreationStates.waiting_for_container_type)
async def container_type_selected(
    callback: CallbackQuery, state: FSMContext, api_client: MyApi = None
):
    await callback.answer()

    container_type = callback.data
    await state.update_data(container_type=container_type)

    data = await state.get_data()
    language = data.get("language", "uz")

    eta = f"{data['eta_date']} {data['eta_hour']}:00"

    api = api_client or MyApi()

    # ✅ 1. Validate live location BEFORE creating Route
    is_valid = await validate_driver_location(
        callback.message, callback.from_user.id, api
    )

    if not is_valid:
        # ❌ Live Location invalid
        # Simply stop the handler (driver will send location and restart creation manually)
        return

    try:
        # ✅ 2. Now safe to create Route
        await api.create_route(
            truck_number=data["truck_number"],
            terminal_id=data["selected_terminal_id"],
            container_name=data["container_name"],
            container_size=data["container_size"],
            container_type=data["container_type"],
            eta=eta,
            telegram_id=callback.from_user.id,
        )

        summary = await build_summary(state, language)

        await callback.message.edit_text(
            f"{summary}\n\n✅ Yo'nalish yaratildi!",
            parse_mode="HTML",
        )

    except Exception as e:
        await callback.message.answer(f"❌ Error creating route: {str(e)}")

    await state.clear()


@route_router.callback_query(F.data == "cancel_route")
async def cancel_route_creation(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    data = await state.get_data()
    language = data.get("language", "uz")

    await state.clear()
    await callback.message.edit_text(CANCEL_TRANSLATIONS[language]["process_canceled"])
