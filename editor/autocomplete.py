"""Python açar sözləri və built-in adları üzrə sadə autocomplete."""
import builtins
import keyword

_WORDS = sorted(set(keyword.kwlist) | set(dir(builtins)))


def suggestions(prefix, limit=8):
    if not prefix:
        return []
    return [word for word in _WORDS if word.startswith(prefix.strip())][:max(0, int(limit))]
