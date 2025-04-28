from datetime import datetime, timezone


async def validate_driver_location(message, telegram_id, api_client):
    """
    Validate if driver's live location is active and fresh.
    """
    latest_location = await api_client.get_latest_location(telegram_id)
    print("Latest location:", latest_location)
    if not latest_location:
        await message.answer(
            "❗️ Joylashuv topilmadi. Iltimos, 📎 Clip tugmasi orqali jonli joylashuv yuboring."
        )
        return False

    timestamp_str = latest_location.get("timestamp")
    live_period = latest_location.get("is_live_period", False)

    if not timestamp_str:
        await message.answer(
            "❗️ Joylashuv vaqti topilmadi. Iltimos, 📎 Clip tugmasi orqali jonli joylashuv yuboring."
        )
        return False

    try:
        timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
    except ValueError:
        await message.answer(
            "❗️ Joylashuv vaqti formati noto'g'ri. Iltimos, qayta jonli joylashuv yuboring."
        )
        return False

    now = datetime.now(timezone.utc)
    time_diff_seconds = (now - timestamp).total_seconds()

    if time_diff_seconds > 60:
        await message.answer(
            "⌛️ Sizning 📍 Jonli joylashuvingiz yangilanishi kechikdi. Iltimos, qayta jonli joylashuv yuboring."
        )
        return False

    if not live_period:
        await message.answer(
            "❗️ Bu jonli joylashuv emas. 📎 Clip tugmasidan foydalanib jonli joylashuv yuboring."
        )
        return False

    return True
