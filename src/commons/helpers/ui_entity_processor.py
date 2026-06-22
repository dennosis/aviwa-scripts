from pathlib import Path
from typing import Optional, Dict, Union, Any
from playwright.async_api import Page
from commons.utils.playwright import redirect_to_url
from commons.utils.urls import bind_url_params, get_unfilled_params
from commons.utils.playwright_with_ui_entity_mapping import (
    get_ui_entity,
    submit_form_on_page,
    get_ui_entity_with_listing,
    get_items_from_listing,
    trigger_global_action,
    trigger_listing_action,
    wait_element_show,
    fill_ui_form,
)


class UiLoginProcessor:
    def __init__(
        self,
        page: Page,
        ui_mapping_path: Union[str | Path],
    ):
        self.page = page
        self.ui_entity = get_ui_entity(ui_mapping_path)

    async def login(self, data: Dict[str, str]):
        await redirect_to_url(self.page, self.ui_entity.url)
        await submit_form_on_page(self.page, self.ui_entity.form, data, "enter")


class UiEntityWithListingProcessor:
    def __init__(
        self,
        page: Page,
        ui_mapping_path: Union[str | Path],
        url_params: Optional[Dict[str, str]] = None,
    ):
        self.page = page
        self.ui_entity = get_ui_entity_with_listing(ui_mapping_path)
        if url_params is not None:
            self.url = bind_url_params(
                self.ui_entity.url,
                url_params,
            )
        else:
            self.url = self.ui_entity.url

        unfilled_params = get_unfilled_params(self.url)

        if len(unfilled_params) > 0:
            raise ValueError(
                f"URL possui parâmetros não preenchidos: {', '.join(unfilled_params)}. "
            )

    async def list_items(self):
        await redirect_to_url(self.page, self.url)
        return await get_items_from_listing(self.page, self.ui_entity)

    async def create_item(self, data: Dict[str, Any]):
        await redirect_to_url(self.page, self.url)
        await trigger_global_action(self.page, self.ui_entity, "create")
        await submit_form_on_page(self.page, self.ui_entity.form, data, "save")

    async def update_item(
        self,
        match: Dict[str, Any],
        data: Dict[str, Any],
    ):
        await redirect_to_url(self.page, self.url)
        await trigger_listing_action(
            self.page,
            self.ui_entity.listing,
            self.ui_entity.pagination,
            "edit",
            match,
        )
        await submit_form_on_page(self.page, self.ui_entity.form, data, "save")


class UiEntityWithListingModalProcessor(UiEntityWithListingProcessor):
    async def create_item(self, data: Dict[str, Any]):
        await redirect_to_url(self.page, self.url)
        await trigger_global_action(self.page, self.ui_entity, "create")
        await wait_element_show(self.page, self.ui_entity.form.element)
        await fill_ui_form(self.page, self.ui_entity.form, data)
        await trigger_global_action(self.page, self.ui_entity, "save_modal_form")

    async def update_item(
        self,
        match: Dict[str, Any],
        data: Dict[str, Any],
    ):
        await redirect_to_url(self.page, self.url)
        await trigger_listing_action(
            self.page,
            self.ui_entity.listing,
            self.ui_entity.pagination,
            "edit",
            match,
        )
        await wait_element_show(self.page, self.ui_entity.form.element)
        await fill_ui_form(self.page, self.ui_entity.form, data)
        await trigger_global_action(self.page, self.ui_entity, "save_modal_form")
