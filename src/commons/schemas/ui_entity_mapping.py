from typing import Dict, Any, List, Optional

from pydantic import BaseModel


class UIIdElement(BaseModel):
    id: Optional[str] = None
    classes: Optional[List[str]] = []


class UIInputIdElement(UIIdElement):
    id_: str
    name: str
    type: str
    label: Optional[str] = None


class UIClickableIdElement(UIIdElement):
    label: Optional[str] = None


class Action(BaseModel):
    id_: str
    trigger: UIClickableIdElement


class UITableColumn(BaseModel):
    id_: str
    label: str
    action: Optional[Action] = None


class UITable(BaseModel):
    element: UIIdElement
    columns: List[UITableColumn]


class UIForm(BaseModel):
    element: UIIdElement
    fields: List[UIInputIdElement]
    actions: List[Action]


class UIPaginate(BaseModel):
    element: UIIdElement
    actions: List[Action]
    current_page: UIIdElement


class UIEntityWithListing(BaseModel):
    url: str
    element: UIIdElement
    listing: UITable
    pagination: UIPaginate
    form: UIForm
    actions: List[Action] = []


class UIEntity(BaseModel):
    url: str
    element: UIIdElement
    form: UIForm
    actions: List[Action] = []


class ScrapingPaginateState(BaseModel):
    pages: List[int]
    current_page: int


class ScrapingListingItem(BaseModel):
    data: Dict[str, Any]
    page: int
    index: int


class ScrapingSelectOption(BaseModel):
    value: str
    label: str
