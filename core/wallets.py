"""
core/wallets.py — крипто-кошельки для вкладки Support в Info-диалоге.

Тексты — через core.i18n.t(). Метки кошельков (BTC, USDT, GRAM) —
не переводим, это имена.
"""

from core.i18n import t


def get_support_title() -> str:
    return t("wallets.support_title")


def get_support_text() -> str:
    return t("wallets.support_text")


# Список кошельков
WALLETS = [
    {
        "label": "BTC",
        "address": "bc1q2ka70s4vtmrskandqj8l4d6n3kdxyxa7kf3wf7",
    },
    {
        "label": "USDT (TRC-20)",
        "address": "TUjY9p6oxKmeCQwNZwMfHqHdXuabaHpgT7",
    },
    {
        "label": "GRAM",
        "address": "UQDWumGNNlnITx48WBzyI7Clb5wrpFRlJ3Se7xhfVKY5E2ad",
    },
]