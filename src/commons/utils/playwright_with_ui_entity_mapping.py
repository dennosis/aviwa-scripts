import re
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Union, Any
from playwright.async_api import Page, Locator
from commons.schemas.ui_entity_mapping import (
    ScrapingListingItem,
    ScrapingPaginateState,
    ScrapingSelectOption,
    UIEntityWithListing,
    UIForm,
    UIIdElement,
    UIPaginate,
    UITable,
    UITableColumn,
    UIEntity,
)
from commons.utils.playwright import check_exist_element
from commons.utils.json import read_json


def _build_selector(element: UIIdElement, text: Optional[str] = None) -> str:
    selector = ""
    if element.id:
        selector += f"#{element.id}"
    if element.classes:
        selector += "".join([f".{c}" for c in element.classes if c])
    if not selector:
        selector = "*"

    if text:
        return f'{selector} >> text="{text}"'
    return selector


async def get_paginate_indexes(page: Page, paginate: UIPaginate) -> List[int]:
    actions_map = {action.id_: action for action in paginate.actions}
    page_action = actions_map.get("page")

    idxs_seletor = _build_selector(page_action.trigger)

    idxs_elements = await page.locator(idxs_seletor).all()

    idxs_numbers = []

    for idx_element in idxs_elements:
        texto = (await idx_element.inner_text()).strip()
        if re.match(page_action.trigger.label, texto):
            idxs_numbers.append(int(texto))

    if len(idxs_numbers) == 0:
        return []
        # raise ValueError("Nenhum índice de página encontrado na paginação.")

    idxs_numbers.sort()

    min_idx = idxs_numbers[0]
    max_idx = idxs_numbers[-1]

    return list(range(min_idx, max_idx + 1))


async def get_current_page_index(page: Page, paginate: UIPaginate) -> int:
    current_page_selector = _build_selector(paginate.current_page)
    current_page_element = page.locator(current_page_selector).first

    current_page_number = None
    if await current_page_element.is_visible():
        page_text = (await current_page_element.inner_text()).strip()
        if page_text.isdigit():
            current_page_number = int(page_text)

    if current_page_number is None:
        raise ValueError("Não foi possível identificar o número da página atual.")

    return current_page_number


async def get_paginate_state(page: Page, paginate: UIPaginate) -> ScrapingPaginateState:

    actions_map = {action.id_: action for action in paginate.actions}
    next_action = actions_map.get("next")
    previous_action = actions_map.get("previous")
    page_action = actions_map.get("page")

    if not next_action or not page_action or not previous_action:
        raise ValueError(
            "A estrutura de paginação precisa conter as actions 'page', 'next' e 'previous'."
        )

    pages_idxs_numbers = await get_paginate_indexes(page, paginate)
    if len(pages_idxs_numbers) == 0:
        return ScrapingPaginateState(pages=pages_idxs_numbers, current_page=-1)

    current_page_number = await get_current_page_index(page, paginate)

    return ScrapingPaginateState(
        pages=pages_idxs_numbers, current_page=current_page_number
    )


async def trigger_next_page(
    page: Page,
    paginate: UIPaginate,
    paginate_state: ScrapingPaginateState,
) -> ScrapingPaginateState:

    actions_map = {action.id_: action for action in paginate.actions}
    next_action = actions_map.get("next")

    next_selector = _build_selector(next_action.trigger)
    await page.locator(next_selector).first.click()
    await page.wait_for_load_state("networkidle")
    current_page_number = await get_current_page_index(page, paginate)

    paginate_state.current_page = current_page_number

    return paginate_state


async def trigger_previous_page(
    page: Page,
    paginate: UIPaginate,
    paginate_state: ScrapingPaginateState,
) -> ScrapingPaginateState:

    actions_map = {action.id_: action for action in paginate.actions}
    previous_action = actions_map.get("previous")

    previous_selector = _build_selector(previous_action.trigger)
    await page.locator(previous_selector).first.click()
    await page.wait_for_load_state("networkidle")
    current_page_number = await get_current_page_index(page, paginate)

    paginate_state.current_page = current_page_number

    return paginate_state


async def trigger_page(
    page: Page,
    paginate: UIPaginate,
    paginate_state: ScrapingPaginateState,
    page_number: int,
) -> ScrapingPaginateState:

    if page_number == paginate_state.current_page:
        return paginate_state

    if page_number not in paginate_state.pages:
        raise ValueError(f"Número de página {page_number} não encontrado na paginação.")

    if page_number > paginate_state.current_page:
        while paginate_state.current_page < page_number:
            paginate_state = await trigger_next_page(page, paginate, paginate_state)

    else:
        while paginate_state.current_page > page_number:
            paginate_state = await trigger_previous_page(page, paginate, paginate_state)

    return paginate_state


async def get_elements_from_table(
    page: Page, table: UITable
) -> Tuple[List[str], List[Locator]]:

    table_selector = _build_selector(table.element)
    table_element = page.locator(table_selector).first

    await check_exist_element(table_element, "tabela")

    columns_labels = (
        await table_element.locator("thead tr").first.locator("th").all_text_contents()
    )

    if len(columns_labels) != len(table.columns):
        raise ValueError("Quantidade de colunas divergentes.")

    for ui_column, m_column in list(
        zip(columns_labels, [t.label for t in table.columns])
    ):
        if ui_column != m_column:
            raise ValueError("Valores de colunas divergentes.")

    rows = await table_element.locator("tbody tr").all()

    return columns_labels, rows


async def get_data_from_row_table(
    row: Locator, columns: List[UITableColumn]
) -> Dict[str, str]:
    row_data = {}
    cells_contents = await row.locator("td").all_text_contents()
    for cell_content, m_id in list(zip(cells_contents, [t.id_ for t in columns])):
        row_data[m_id] = cell_content
    return row_data


async def iter_paginate(page: Page, paginate: UIPaginate):

    paginate_state = await get_paginate_state(page, paginate)

    if len(paginate_state.pages) == 0:
        return

    first_page = paginate_state.pages[0]
    if first_page != paginate_state.current_page:
        paginate_state = await trigger_page(page, paginate, paginate_state, first_page)

    for page_idx in paginate_state.pages:
        yield page_idx
        paginate_state = await trigger_next_page(page, paginate, paginate_state)


async def iter_rows_table(page: Page, table: UITable):
    _, rows = await get_elements_from_table(page, table)
    for i, row in enumerate(rows):
        yield i, row


async def iter_rows_table_with_paginate(
    page: Page, table: UITable, paginate: UIPaginate
):
    async for page_number in iter_paginate(page, paginate):
        async for row_index, row in iter_rows_table(page, table):
            yield page_number, row_index, row


async def get_data_single_table(page: Page, table: UITable) -> List[Dict[str, str]]:
    data = []
    async for _, row in iter_rows_table(page, table):
        row_data = await get_data_from_row_table(row, table.columns)
        data.append(row_data)
    return data


async def get_items_from_listing(
    page: Page, ui_entity: UIEntityWithListing
) -> List[ScrapingListingItem]:

    data = []
    async for page_number in iter_paginate(page, ui_entity.pagination):
        data_table = await get_data_single_table(page, ui_entity.listing)
        for i, d_table in enumerate(data_table):
            if len(d_table) == 0:
                continue
            data.append(
                ScrapingListingItem.model_validate(
                    {
                        "data": d_table,
                        "page": page_number,
                        "index": i,
                    }
                )
            )

    return data


async def wait_element_show(
    page: Page,
    element: UIIdElement,
):
    await page.wait_for_selector(
        _build_selector(element), state="visible", timeout=10000
    )


async def trigger_global_action(
    page: Page,
    ui_entity: UIEntityWithListing,
    id: str,
):
    actions_map = {action.id_: action for action in ui_entity.actions}
    action = actions_map.get(id)

    if not action:
        raise ValueError(f"A ação '{id}' não esta mapeada.")

    action_selector = _build_selector(action.trigger, action.trigger.label)
    action_element = page.locator(action_selector).first

    if not await action_element.is_visible():
        raise ValueError(f"A ação '{id}' não esta sendo encontrada")

    await action_element.click()

    await page.wait_for_load_state("networkidle")


async def trigger_form_action(page: Page, ui_form: UIForm, id: str):

    form_selector = _build_selector(ui_form.element)
    form_element = page.locator(form_selector).first

    await check_exist_element(form_element, "formulario")

    actions_map = {action.id_: action for action in ui_form.actions}
    action = actions_map.get(id)

    if not action:
        raise ValueError(f"A ação '{id}' não esta mapeada.")

    action_selector = _build_selector(action.trigger, action.trigger.label)
    action_element = form_element.locator(action_selector).first

    if not await action_element.is_visible():
        raise ValueError(f"A ação '{id}' não esta sendo encontrada")

    await action_element.click()

    await page.wait_for_load_state("networkidle")


async def trigger_listing_action(
    page: Page,
    ui_listing: UITable,
    paginate: UIPaginate,
    id: str,
    match: Dict[str, str],
):
    cols_actions_map = {
        col.action.id_: (i_col, col.action)
        for i_col, col in enumerate(ui_listing.columns)
        if col.action is not None
    }
    col_action_map = cols_actions_map.get(id)
    if col_action_map is None:
        raise ValueError(f"A ação '{id}' não esta mapeada.")

    col_index, col_action = col_action_map

    matched = False
    async for _, _, row in iter_rows_table_with_paginate(page, ui_listing, paginate):
        row_data = await get_data_from_row_table(row, ui_listing.columns)

        if match.items() <= row_data.items():
            row_cols = await row.locator("td").all()
            row_col = row_cols[col_index]

            action_selector = _build_selector(
                col_action.trigger, col_action.trigger.label
            )
            action_element = row_col.locator(action_selector).first

            await check_exist_element(action_element, id)

            await action_element.click()

            await page.wait_for_load_state("networkidle")

            matched = True
            break

    if not matched:
        raise ValueError("A linha não pode ser identificada, verificar o 'match'.")


async def get_options_from_select(
    select_locator: Locator,
) -> List[ScrapingSelectOption]:
    options_dict = await select_locator.evaluate("""
        select => Array.from(select.options).map(option => ({
            value: option.value,
            label: option.text.trim()
        }))
    """)

    return [ScrapingSelectOption(**opt) for opt in options_dict]


async def fill_ui_form(
    page: Page,
    ui_form: UIForm,
    data: Dict[str, Union[str, float, int, bool, Path, List[Path]]],
) -> bool:

    form_selector = _build_selector(ui_form.element)
    form_element = page.locator(form_selector).first

    await check_exist_element(form_element, "formulario")

    fields_map = {field.id_: field for field in ui_form.fields}

    keys_not_mapped = [key for key in data.keys() if key not in fields_map]

    if len(keys_not_mapped) > 0:
        keys_not_mapped_str = ", ".join([f"'{key}'" for key in keys_not_mapped])
        raise ValueError(f"Os campos {keys_not_mapped_str} não estão mapeados.")

    for field_id, field_value in data.items():
        field_m = fields_map[field_id]

        if field_m.type in [
            "text",
            "password",
            "hidden",
            "text_area_modal",
            "textarea",
        ]:
            if not isinstance(field_value, str):
                raise ValueError(f"O campo {field_id} possui valor inválido.")

            if field_m.type == "textarea":
                text_element = form_element.locator(
                    f"textarea[name='{field_m.name}']"
                ).first

            else:
                text_element = form_element.locator(
                    f"input[name='{field_m.name}']"
                ).first

            await check_exist_element(text_element, field_m.name)

            input_type = await text_element.get_attribute("type")
            if input_type == "hidden":
                await text_element.evaluate(
                    """(el, value) => {
                        el.value = value;
                        el.dispatchEvent(new Event('input', { bubbles: true }));
                        el.dispatchEvent(new Event('change', { bubbles: true }));
                    }""",
                    field_value,
                )
            else:
                await text_element.fill(field_value)

        if field_m.type == "number":
            if not isinstance(field_value, (int, float)):
                raise ValueError(f"O campo {field_id} possui valor inválido.")
            number_element = form_element.locator(f"input[name='{field_m.name}']").first
            await check_exist_element(number_element, field_m.name)
            await number_element.fill(str(field_value))

        elif field_m.type == "select":
            if not isinstance(field_value, str):
                raise ValueError(f"O campo {field_id} possui valor inválido.")
            select_element = form_element.locator(
                f"select[name='{field_m.name}']"
            ).first
            await check_exist_element(select_element, field_m.name)
            select_options = await get_options_from_select(select_element)
            if len(select_options) == 0:
                raise ValueError(f"O campo {field_id} não possui opções.")
            if field_value in [opt.value for opt in select_options]:
                option_to_select = field_value
            else:
                matched = next(
                    (opt for opt in select_options if opt.label == field_value),
                    None,
                )
                if matched is None:
                    raise ValueError(
                        f"O campo {field_id} não possui a opção {field_value}."
                    )
                option_to_select = matched.value

            await select_element.select_option(option_to_select)

        elif field_m.type == "file":
            if isinstance(field_value, (str, Path)):
                paths: List[Path] = [Path(field_value)]
            elif isinstance(field_value, list):
                paths = [Path(p) for p in field_value]
            else:
                raise ValueError(f"O campo {field_id} possui valor inválido.")

            for path in paths:
                if not path.exists():
                    raise ValueError(
                        f"O arquivo '{path}' não foi encontrado para o campo {field_id}."
                    )

            file_element = form_element.locator(f"input[name='{field_m.name}']").first
            await check_exist_element(file_element, field_m.name)

            is_multiple = await file_element.get_attribute("multiple")
            if is_multiple is None and len(paths) > 1:
                raise ValueError(f"O campo {field_id} não aceita múltiplos arquivos.")

            await file_element.set_input_files([str(p) for p in paths])

        elif field_m.type == "checkbox":
            if not isinstance(field_value, bool):
                raise ValueError(f"O campo {field_id} possui valor inválido.")
            check_element = form_element.locator(f"input[name='{field_m.name}']").first
            await check_exist_element(check_element, field_m.name)
            if field_value:
                await check_element.check()
            else:
                await check_element.uncheck()


async def submit_form_on_page(
    page: Page,
    ui_form: UIForm,
    data: Dict[str, Any],
    id: str,
):
    await fill_ui_form(page, ui_form, data)

    await trigger_form_action(page, ui_form, id)


def get_ui_entity(path: Union[str | Path]) -> UIEntity:
    ui_mapping = read_json(path)
    return UIEntity.model_validate(ui_mapping)


def get_ui_entity_with_listing(path: Union[str | Path]) -> UIEntityWithListing:
    ui_mapping = read_json(path)
    return UIEntityWithListing.model_validate(ui_mapping)
