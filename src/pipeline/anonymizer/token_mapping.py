from collections import defaultdict


class TokenMapper:
    def __init__(self):
        self._mappings: dict[str, dict[str, str]] = defaultdict(dict)
        self._counters: dict[str, int] = defaultdict(int)

    def get_or_create_token(self, entity_type: str, original_value: str) -> str:
        for token, value in self._mappings[entity_type].items():
            if value == original_value:
                return token

        self._counters[entity_type] += 1
        token = f"<{entity_type}_{self._counters[entity_type]}>"
        self._mappings[entity_type][token] = original_value
        return token

    def resolve(self, token: str) -> str | None:
        for mappings in self._mappings.values():
            if token in mappings:
                return mappings[token]
        return None

    def get_all_mappings(self) -> dict[str, dict[str, str]]:
        return dict(self._mappings)
