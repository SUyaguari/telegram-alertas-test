import asyncio
from datetime import datetime, timedelta, timezone
import json
import logging
import re
import unicodedata

from telethon import errors


LOGGER = logging.getLogger("telegram_alertas")
LOOKBACK_DAYS = 14
MESSAGES_PER_GROUP = 60
FORMATS_PER_GROUP = 10
MONEY = re.compile(
    r"[$€]\s*\d|\bUSD[TC]?\s*\d"
    r"|\d[\d., ]*\s*(?:[KMB]|mil|万|亿)?\s*(?:USD[TC]?|d[oó]lares?)\b",
    re.IGNORECASE,
)
TOKEN = re.compile(r"\$[A-Z][A-Z0-9_]{1,19}\b")
MOVEMENT = re.compile(
    r"交易所|转账|轉賬|流[入出]|大[额額]|买入|卖出|取引所|거래소|유입|유출|бирж|перевод|بورص|تحويل"
    r"|\b(?:exchanges?|transfers?|transferencias?|transf[eê]rencias?|transferts?|"
    r"whales?|ballenas?|baleias?|outflows?|inflows?|withdrawals?|deposits?|"
    r"retiros?|dep[oó]sitos?|liquidations?|liquidaciones?|on.chain|swaps?|"
    r"compras?|ventas?|buy|sell|wallets?|billeteras?)\b",
    re.IGNORECASE,
)
IDENTIFIERS = re.compile(
    r"(?:https?://|www\.|t\.me/)\S+"
    r"|[\w.+-]+@[\w.-]+\.[a-z]{2,}"
    r"|(?<!\w)@[A-Za-z0-9_]{4,}"
    r"|\b0x[0-9a-f]{16,}\b"
    r"|(?<!\w)\+[0-9][0-9 ()-]{8,}[0-9]",
    re.IGNORECASE,
)


def candidate(text):
    text = unicodedata.normalize("NFKC", text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return None
    excerpt = "\n".join(lines[:14])[:1800]
    has_money = bool(MONEY.search(excerpt))
    has_token = bool(TOKEN.search(excerpt))
    has_movement = bool(MOVEMENT.search(excerpt))
    if not (
        (has_money and (has_token or has_movement))
        or (has_token and has_movement and any(char.isdigit() for char in excerpt))
    ):
        return None
    excerpt = IDENTIFIERS.sub("[oculto]", excerpt)
    signature = re.sub(r"\$[A-Z][A-Z0-9_]{1,19}\b", "$TOKEN", excerpt)
    signature = re.sub(r"\d+(?:[.,]\d+)*", "#", signature)
    signature = re.sub(r"\s+", " ", signature).strip().casefold()
    return signature, excerpt


async def sample_groups(client, state_dir):
    cutoff = datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)
    destination = state_dir / "muestras-formatos.json"
    groups = []
    error = None
    LOGGER.info("Revisando formatos recientes de los grupos. La escucha sigue activa.")
    try:
        async for dialog in client.iter_dialogs(ignore_migrated=True):
            if not dialog.is_group or (dialog.date and dialog.date < cutoff):
                continue
            if getattr(dialog.entity, "noforwards", False):
                continue
            formats = {}
            scanned = 0
            group_error = None
            try:
                async for message in client.iter_messages(dialog.input_entity, limit=MESSAGES_PER_GROUP):
                    if not message.date or message.date < cutoff:
                        break
                    if message.out or not message.raw_text or getattr(message, "noforwards", False):
                        continue
                    scanned += 1
                    result = candidate(message.raw_text)
                    if not result:
                        continue
                    signature, excerpt = result
                    if signature in formats:
                        formats[signature]["count"] += 1
                    elif len(formats) < FORMATS_PER_GROUP:
                        formats[signature] = {"count": 1, "text": excerpt}
            except errors.FloodWaitError as exc:
                group_error = f"Telegram pidió esperar {exc.seconds} segundos"
                error = group_error
            except errors.RPCError as exc:
                group_error = type(exc).__name__
            groups.append({
                "group": dialog.name, "messagesReviewed": scanned,
                "formats": list(formats.values()), "error": group_error,
            })
            if error:
                break
            await asyncio.sleep(0.4)
    except errors.FloodWaitError as exc:
        error = f"Telegram pidió esperar {exc.seconds} segundos"
    except Exception as exc:
        error = type(exc).__name__
        LOGGER.exception("Se interrumpió el muestreo.")
    report = {
        "days": LOOKBACK_DAYS, "limitPerGroup": MESSAGES_PER_GROUP, "error": error,
        "groups": groups,
    }
    try:
        draft = destination.with_suffix(".tmp")
        draft.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        draft.replace(destination)
    except OSError:
        LOGGER.exception("No se pudo guardar la muestra de formatos.")
        return
    count = sum(len(group["formats"]) for group in groups)
    LOGGER.info("Muestra %s: %s grupos, %s formatos.", "parcial" if error else "lista", len(groups), count)
