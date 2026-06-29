from pathlib import Path
from typing import Optional, Dict, Union, Any
from playwright.async_api import Page
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
    redirect_to_url_and_wait_element_show,
    wait_element_table_show,
    CustomFill,
)
from commons.utils.dict import MatchType


class UiLoginProcessor:
    def __init__(
        self,
        page: Page,
        ui_mapping_path: Union[str | Path],
    ):
        self.page = page
        self.ui_entity = get_ui_entity(ui_mapping_path)

    async def login(self, data: Dict[str, str]):
        await redirect_to_url_and_wait_element_show(
            self.page, self.ui_entity.url, self.ui_entity.element
        )
        await submit_form_on_page(self.page, self.ui_entity.form, data, "enter")


class UiEntityWithListingProcessor:
    def __init__(
        self,
        page: Page,
        ui_mapping_path: Union[str | Path],
        url_params: Optional[Dict[str, str]] = None,
        custom_fill: Optional[CustomFill] = None,
    ):
        self.page = page
        self.ui_entity = get_ui_entity_with_listing(ui_mapping_path)
        self.custom_fill = custom_fill
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

    async def redirect_to_page(self):
        await redirect_to_url_and_wait_element_show(
            self.page, self.url, self.ui_entity.element
        )

    async def list_items(self):
        await self.redirect_to_page()
        await wait_element_table_show(
            self.page, self.ui_entity.listing.element, ".dataTables_empty"
        )
        return await get_items_from_listing(self.page, self.ui_entity)

    async def create_item(self, data: Dict[str, Any]):
        await self.redirect_to_page()
        await trigger_global_action(self.page, self.ui_entity, "create")
        await submit_form_on_page(
            self.page, self.ui_entity.form, data, "save", self.custom_fill
        )

    async def update_item(
        self,
        data: Dict[str, Any],
        match: Dict[str, Any],
        match_type: Optional[MatchType] = None,
    ):
        await self.redirect_to_page()
        await trigger_listing_action(
            self.page,
            self.ui_entity.listing,
            self.ui_entity.pagination,
            "edit",
            match,
            match_type,
        )
        await submit_form_on_page(
            self.page, self.ui_entity.form, data, "save", self.custom_fill
        )


class UiEntityWithListingModalProcessor(UiEntityWithListingProcessor):
    async def create_item(self, data: Dict[str, Any]):
        await self.redirect_to_page()
        await trigger_global_action(self.page, self.ui_entity, "create")
        await wait_element_show(self.page, self.ui_entity.form.element)
        await fill_ui_form(self.page, self.ui_entity.form, data, self.custom_fill)
        await trigger_global_action(self.page, self.ui_entity, "save_modal_form")

    async def update_item(
        self,
        data: Dict[str, Any],
        match: Dict[str, Any],
        match_type: Optional[MatchType] = None,
    ):
        await self.redirect_to_page()
        await trigger_listing_action(
            self.page,
            self.ui_entity.listing,
            self.ui_entity.pagination,
            "edit",
            match,
            match_type,
        )
        await wait_element_show(self.page, self.ui_entity.form.element)
        await fill_ui_form(self.page, self.ui_entity.form, data, self.custom_fill)
        await trigger_global_action(self.page, self.ui_entity, "save_modal_form")
