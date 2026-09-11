"""
Funzioni di utilità del Bot Telegram.
"""


def format_search_terms(context):
    """
    Restituisce gli argomenti utilizzati dopo il comando.
    """

    args = getattr(context, "args", None)

    if not args:
        return "nessun termine"

    return " ".join(args)


def format_user(user):
    """
    Restituisce un identificativo leggibile dell'utente
    per i log.
    """

    if not user:
        return "utente sconosciuto"

    if user.username:
        return f"@{user.username}"

    if user.full_name:
        return user.full_name

    return f"id={user.id}"