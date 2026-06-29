def format_number_ptbr(value: int | float, decimal_places: int = 0) -> str:
    formatted = f"{value:,.{decimal_places}f}"
    return formatted.replace(",", "X").replace(".", ",").replace("X", ".")
