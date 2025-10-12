# src/common/tz.py
from datetime import datetime, timezone, timedelta

# Tenta zoneinfo (preferido)
try:
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
    try:
        TZ = ZoneInfo("America/Sao_Paulo")
    except ZoneInfoNotFoundError:
        # Sem tzdata instalado: faz fallback
        raise ImportError("tzdata ausente para zoneinfo")
except Exception:
    # Fallbacks: tenta dateutil, senão offset fixo (-03:00)
    try:
        from dateutil.tz import gettz  # pip install python-dateutil (já vem com FastAPI)
        TZ = gettz("America/Sao_Paulo") or timezone(timedelta(hours=-3))
    except Exception:
        TZ = timezone(timedelta(hours=-3))  # sem DST (ok desde 2019)

def now_sp() -> datetime:
    """Retorna datetime aware em America/Sao_Paulo."""
    return datetime.now(TZ)
