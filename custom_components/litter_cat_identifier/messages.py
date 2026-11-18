"""Notification texts (English + Spanish, picked from the HA language)."""

from __future__ import annotations

_TEXTS = {
    "en": {
        "visit": "{cat} used the litter box{weight}.",
        "unidentified_partial_after_visit": "Unidentified reading{weight}: probably {cat} half inside, right after the visit.",
        "unidentified_refill_or_partial": "Unidentified reading{weight}: probably a litter refill or a cat half inside.",
        "unidentified_no_weight": "A visit was detected but no weight was reported.",
        "inactive": "{cat} hasn't used the litter box for over {hours} h.",
        "unidentified_device_busy": "Unidentified reading{weight}: the litter box was moving the litter (cleaning, emptying or levelling).",
        "unidentified_stayed_too_long": "Unidentified reading{weight}: a cat stayed too long, the litter box levelled the litter and reset the weight.",
        "health_frequent_visits": "{cat} has used the litter box {count} times today, much more than usual. If it continues, consider a vet check.",
        "health_long_visit": "{cat} stayed {seconds} s in the litter box, much longer than usual.",
        "health_weight_loss": "{cat} has lost {pct} % of their weight in the last weeks.",
    },
    "es": {
        "visit": "{cat} ha usado el arenero{weight}.",
        "unidentified_partial_after_visit": "Lectura no identificada{weight}: probablemente {cat} medio dentro, justo tras su visita.",
        "unidentified_refill_or_partial": "Lectura no identificada{weight}: probablemente relleno de arena o un gato medio dentro.",
        "unidentified_no_weight": "Se detectó una visita pero sin peso.",
        "inactive": "{cat} lleva más de {hours} h sin usar el arenero.",
        "unidentified_device_busy": "Lectura no identificada{weight}: el arenero estaba moviendo la arena (limpiando, vaciando o nivelando).",
        "unidentified_stayed_too_long": "Lectura no identificada{weight}: un gato estuvo demasiado tiempo, el arenero niveló la arena y reinició el peso.",
        "health_frequent_visits": "{cat} ha usado el arenero {count} veces hoy, mucho más de lo habitual. Si sigue así, consulta al veterinario.",
        "health_long_visit": "{cat} ha estado {seconds} s en el arenero, mucho más de lo habitual.",
        "health_weight_loss": "{cat} ha perdido un {pct} % de peso en las últimas semanas.",
    },
}


def text(language: str | None, key: str, **kwargs: object) -> str:
    lang = (language or "en").split("-")[0].lower()
    template = _TEXTS.get(lang, _TEXTS["en"])[key]
    weight = kwargs.pop("weight", None)
    weight_str = f" ({weight:.2f} kg)" if isinstance(weight, (int, float)) else ""
    return template.format(weight=weight_str, **kwargs)
