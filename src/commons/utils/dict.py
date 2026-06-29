from typing import Any, Literal, Iterable, Dict, Optional


MatchType = Literal["equals", "contains"]


def is_match(
    data_value: Any, search_value: Any, match_type: Optional[MatchType] = None
) -> bool:

    if match_type is None:
        match_type = "equals"

    if data_value is None:
        return False
    if match_type == "equals":
        return data_value == search_value
    elif match_type == "contains":
        try:
            return search_value in data_value
        except TypeError:
            return False
    return False


def is_match_dict(
    data: dict[str, Any], match: dict[str, Any], match_type: Optional[MatchType] = None
) -> bool:
    return all(is_match(data.get(k), v, match_type) for k, v in match.items())


def subdict(data: Dict[str, Any], keys: Iterable[str]) -> Dict[str, Any]:
    return {k: data[k] for k in keys if k in data}
