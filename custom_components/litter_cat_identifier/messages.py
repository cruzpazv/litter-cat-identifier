"""Notification texts (English + Spanish, picked from the HA language)."""

from __future__ import annotations

_TEXTS = {
    "en": {
        "visit": "{cat} used the litter box{weight}.",
        "unidentified": "An unidentified cat used the litter box{weight}.",
        "inactive": "{cat} hasn't used the litter box for over {hours} h.",
    },
    "es": {
        "visit": "{cat} ha usado el arenero{weight}.",
        "unidentified": "Un gato no identificado ha usado el arenero{weight}.",
        "inactive": "{cat} lleva más de {hours} h sin usar el arenero.",
    },
}


def text(language: str | None, key: str, **kwargs: object) -> str:
    lang = (language or "en").split("-")[0].lower()
    template = _TEXTS.get(lang, _TEXTS["en"])[key]
    weight = kwargs.pop("weight", None)
    weight_str = f" ({weight:.2f} kg)" if isinstance(weight, (int, float)) else ""
    return template.format(weight=weight_str, **kwargs)
