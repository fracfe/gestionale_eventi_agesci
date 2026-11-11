"""Autorizzazioni applicate anche agli endpoint JSON, non solo alla UI."""
from flask import abort
from flask_login import current_user


def permissions():
    from app import db
    from models import GruppiUser
    if not current_user.is_authenticated:
        return set()
    group = db.session.get(GruppiUser, current_user.gruppo)
    return set(group.permessi or []) if group else set()


def require_permission(name):
    if name not in permissions():
        abort(403)


def event_for_user(event_id):
    from app import db
    from models import Evento
    require_permission("EVENTS")
    try:
        event_id = int(event_id)
    except (TypeError, ValueError):
        abort(404)
    event = db.session.get(Evento, event_id)
    if event is None:
        abort(404)
    allowed = permissions()
    if "ALL_EVENTS" not in allowed and not (
        "MY_EVENTS" in allowed and event.responsabile == current_user.id
    ):
        abort(403)
    return event


def can_assign(user_id):
    from app import db
    from models import User
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        abort(400)
    if db.session.get(User, user_id) is None:
        abort(400)
    allowed = permissions()
    if "ALL_EVENTS" not in allowed and not (
        "MY_EVENTS" in allowed and user_id == current_user.id
    ):
        abort(403)
