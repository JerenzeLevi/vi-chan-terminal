"""Shared session state plus usage / rate-limit tracking."""
import time

from .config import CONTEXT_WINDOWS
from .ui import fmt_n


class State:
    cfg = None
    client = None
    model = None
    provider = None  # provider id, e.g. "openai" or "custom:host"
    stream_usage = True  # ask the provider for token usage in streams
    plan_mode = False
    session_auto_approve = False
    messages = []
    mcp = None
    session_in = 0
    session_out = 0
    requests = 0
    ctx_tokens = 0  # size of the latest prompt = how full the context is
    limits = {}  # rate-limit headers from the last response
    limited_until = 0.0


state = State()


def ctx_window():
    m = (state.model or "").lower()
    return next((w for k, w in CONTEXT_WINDOWS if k in m), 128_000)


def ctx_pct():
    return min(100, round(100 * state.ctx_tokens / ctx_window()))


def ctx_bar(width=20):
    filled = round(width * ctx_pct() / 100)
    return "▰" * filled + "▱" * (width - filled)


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def limit_pairs():
    """[(label, remaining, limit)] parsed from whatever rate-limit headers the provider sent."""
    out = []
    for kind in ("requests", "tokens"):
        for rem_key, lim_key in (
            (f"x-ratelimit-remaining-{kind}", f"x-ratelimit-limit-{kind}"),
            (f"anthropic-ratelimit-{kind}-remaining", f"anthropic-ratelimit-{kind}-limit"),
        ):
            rem = _num(state.limits.get(rem_key))
            if rem is not None:
                out.append((kind, rem, _num(state.limits.get(lim_key))))
                break
    return out


def limit_status():
    """(level, text) where level is ok | low | limited."""
    now = time.time()
    if state.limited_until > now:
        return "limited", f"✖ limited · retry in {int(state.limited_until - now)}s"
    pairs = limit_pairs()
    if not pairs:
        return "ok", "✓ limits ok"
    low = any(lim and rem / lim < 0.1 for _, rem, lim in pairs)
    txt = " ".join(f"{lbl[:3]} {fmt_n(rem)}" + (f"/{fmt_n(lim)}" if lim else "") for lbl, rem, lim in pairs)
    return ("low", f"⚠ {txt}") if low else ("ok", f"✓ {txt}")


def record_headers(headers):
    state.limits = {k.lower(): v for k, v in headers.items() if "ratelimit" in k.lower() or k.lower() == "retry-after"}
