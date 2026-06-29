from typing import List, Optional
from enum import Enum
from pydantic import BaseModel


class ArtDimension(BaseModel):
    name: Optional[str] = None
    width: float
    height: float
    depth: Optional[float] = None
    weight: Optional[float] = None


class ArtType(Enum):
    DIGITAL = "digital"
    SCULPTURE = "escultura"
    PAINTING = "pintura"


class AvwArt(BaseModel):
    id: str
    name: str
    raw_description: Optional[str] = None
    image_urls: List[str]
    detailed_image_url: Optional[str] = None
    artist_name: str
    collection_name: Optional[str] = None
    dimensions: List[ArtDimension]
    colors_tags: List[str]
    materials_tags: List[str]
    code: str
    year: Optional[int] = None
    delivery_information: str
    stock_information: str
    presentation_text: Optional[str] = None
    type: ArtType
    url: str
    extra_description: str
    price: float
