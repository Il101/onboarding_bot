from datetime import datetime, timedelta


def group_messages_chronologically(messages: list, window_minutes: int = 30) -> list[list]:
    if not messages:
        return []

    groups = []
    current_group = [messages[0]]
    prev_time = _parse_date(messages[0].date)

    for msg in messages[1:]:
        msg_time = _parse_date(msg.date)
        if (msg_time - prev_time) > timedelta(minutes=window_minutes):
            groups.append(current_group)
            current_group = [msg]
        else:
            current_group.append(msg)
        prev_time = msg_time

    if current_group:
        groups.append(current_group)

    return groups


def _parse_date(date_str: str) -> datetime:
    return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
