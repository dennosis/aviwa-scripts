from typing import Dict
import re


def bind_url_params(url: str, params: Dict[str, str]) -> str:
    """
    Substitui parâmetros na URL no formato {{param_name}} pelos valores do dict.

    Args:
        url: URL com placeholders no formato {{param_name}}
        params: Dict com os valores a substituir

    Returns:
        URL com os parâmetros substituídos

    Raises:
        KeyError: Se uma chave do dict não for encontrada na URL
        ValueError: Se a URL contiver placeholders não fornecidos no dict
    """
    for key in params:
        placeholder = f"{{{{{key}}}}}"
        if placeholder not in url:
            raise KeyError(f"Parâmetro '{key}' não encontrado na URL: {url}")

    placeholders_in_url = re.findall(r"\{\{(\w+)\}\}", url)
    for placeholder in placeholders_in_url:
        if placeholder not in params:
            raise ValueError(
                f"Placeholder '{{{{{placeholder}}}}}' na URL não foi fornecido no dict"
            )

    result = url
    for key, value in params.items():
        result = result.replace(f"{{{{{key}}}}}", str(value))

    return result


def get_unfilled_params(url: str) -> list[str]:
    """
    Retorna os nomes dos parâmetros não preenchidos.
    """
    return re.findall(r"\{\{([^{}]+)\}\}", url)
