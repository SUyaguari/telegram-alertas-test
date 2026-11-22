import asyncio
import getpass
import json
import logging
import os
from pathlib import Path
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from telethon import TelegramClient, events


WEBHOOK_URL = "http://localhost:5678/webhook/telegram-personal-alertas"
STATE_DIR = Path(os.environ["LOCALAPPDATA"]) / "TelegramAlertasN8n"
LOGGER = logging.getLogger("telegram_alertas")


def personal_phone():
    while True:
        entered = input("Número de tu cuenta personal de Telegram (+código de país): ")
        number = re.sub(r"[\s()-]+", "", entered)
        if re.fullmatch(r"\+[1-9][0-9]{6,14}", number):
            return number
        print("Ingresa el número con + y código de país, por ejemplo +593 seguida de tu número.")


def evaluate(message, token):
    request = Request(
        WEBHOOK_URL,
        data=json.dumps(message).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-Telegram-Bridge-Key": token},
        method="POST",
    )
    with urlopen(request, timeout=15) as response:
        result = json.load(response)
    if not isinstance(result, dict) or type(result.get("alert")) is not bool:
        raise ValueError("Respuesta inesperada de n8n")
    if result["alert"] and not isinstance(result.get("text"), str):
        raise ValueError("La alerta no trae texto")
    return result


def telegram_parts(text, limit=4096):
    start = size = 0
    for index, char in enumerate(text):
        units = 2 if ord(char) > 0xFFFF else 1
        if size + units > limit:
            yield text[start:index]
            start, size = index, 0
        size += units
    if start < len(text):
        yield text[start:]


async def main():
    token = os.environ.pop("N8N_TELEGRAM_BRIDGE_KEY")
    api_id = int(input("API ID de Telegram: ").strip())
    api_hash = getpass.getpass("API hash de Telegram: ").strip()
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    client = TelegramClient(str(STATE_DIR / "cuenta-usuario"), api_id, api_hash)

    async def receive(event):
        if not event.is_group or not event.raw_text:
            return
        chat = await event.get_chat()
        message = {
            "chatType": "group",
            "chatId": str(event.chat_id),
            "group": getattr(chat, "title", None),
            "messageId": event.id,
            "message": event.raw_text,
        }
        for attempt in range(3):
            try:
                result = await asyncio.to_thread(evaluate, message, token)
                break
            except HTTPError as error:
                if error.code < 500 or attempt == 2:
                    LOGGER.error("n8n respondió HTTP %s para el mensaje %s.", error.code, event.id)
                    return
            except (URLError, TimeoutError, ValueError) as error:
                if attempt == 2:
                    LOGGER.error("No se pudo procesar el mensaje %s (%s).", event.id, type(error).__name__)
                    return
            await asyncio.sleep(2 ** attempt)
        if result["alert"]:
            for part in telegram_parts(result["text"]):
                await client.send_message("me", part, parse_mode=None, link_preview=False)

    try:
        await client.start(
            phone=personal_phone,
            code_callback=lambda: getpass.getpass("Código de inicio de sesión de Telegram: ").strip(),
            password=lambda: getpass.getpass("Contraseña de verificación en dos pasos: "),
        )
        account = await client.get_me()
        if account is None or account.bot:
            raise SystemExit("Se necesita una sesión de cuenta personal de Telegram.")

        client.add_event_handler(receive, events.NewMessage(incoming=True))
        LOGGER.info("Cuenta personal de Telegram conectada. Las alertas llegarán a Mensajes guardados.")
        if "--revisar-formatos" in sys.argv:
            from revisar_formatos import sample_groups

            review = asyncio.create_task(sample_groups(client, STATE_DIR))
            try:
                await client.run_until_disconnected()
            finally:
                if not review.done():
                    review.cancel()
                await asyncio.gather(review, return_exceptions=True)
        else:
            await client.run_until_disconnected()
    finally:
        await client.disconnect()


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    LOGGER.setLevel(logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
