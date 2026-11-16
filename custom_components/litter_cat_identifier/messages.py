"""Notification texts (English + Spanish, picked from the HA language)."""

from __future__ import annotations

_TEXTS = {
    "en": {
        "visit": "{cat} used the litter box{weight}.",
        "unidentified_partial_after_visit": "Unidentified reading{weight}: probably {cat} half inside, right after the visit.",
        "unidentified_refill_or_partial": "Unidentified reading{weight}: probably a litter refill or a cat half inside.",
        "unidentified_no_weight": "A visit was detected but no weight was reported.",
        "inactive": "{cat} hasn't used the litter box for over {hours} h.",
    },
    "es": {
        "visit": "{cat} ha usado el arenero{weight}.",
        "unidentified_partial_after_visit": "Lectura no identificada{weight}: probablemente {cat} medio dentro, justo tras su visita.",
        "unidentified_refill_or_partial": "Lectura no identificada{weight}: probablemente relleno de arena o un gato medio dentro.",
        "unidentified_no_weight": "Se detectó una visita pero sin peso.",
        "inactive": "{cat} lleva más de {hours} h sin usar el arenero.",
    },
}


def text(language: str | None, key: str, **kwargs: object) -> str:
    lang = (language or "en").split("-")[0].lower()
    template = _TEXTS.get(lang, _TEXTS["en"])[key]
    weight = kwargs.pop("weight", None)
    weight_str = f" ({weight:.2f} kg)" if isinstance(weight, (int, float)) else ""
    return template.format(weight=weight_str, **kwargs)
