"""
Database Schemas for Car Brand Website

Each Pydantic model represents a collection in MongoDB. The collection name is the lowercase of the class name.

- CarModel -> "carmodel"
- Promotion -> "promotion"
- Dealer -> "dealer"
- Lead -> "lead"

These schemas are used for request/response validation and for creating documents via the helper functions.
"""
from __future__ import annotations
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional

# Core domain models

class Variant(BaseModel):
    name: str = Field(..., description="Trim/variant name")
    engine: str = Field(..., description="Engine description")
    transmission: str = Field(..., description="Transmission type")
    drivetrain: Optional[str] = Field(None, description="Drivetrain (e.g., FWD, RWD, AWD)")
    price: float = Field(..., ge=0, description="Base price for this variant")

class Spec(BaseModel):
    dimensions: Optional[dict] = Field(default_factory=dict)
    engine: Optional[dict] = Field(default_factory=dict)
    performance: Optional[dict] = Field(default_factory=dict)
    safety: Optional[List[str]] = Field(default_factory=list)
    features: Optional[List[str]] = Field(default_factory=list)

class MediaAsset(BaseModel):
    url: str
    type: str = Field("image", description="image | video | document")
    title: Optional[str] = None
    thumbnail: Optional[str] = None

class PriceRange(BaseModel):
    min: float = Field(..., ge=0)
    max: float = Field(..., ge=0)
    currency: str = Field("USD")

class CarModel(BaseModel):
    name: str
    slug: str = Field(..., description="URL-friendly identifier")
    body_type: str = Field(..., description="e.g., Hatchback, Sedan, SUV")
    fuel_type: str = Field(..., description="e.g., Petrol, Diesel, EV, Hybrid")
    hero_image: Optional[str] = None
    gallery: List[MediaAsset] = Field(default_factory=list)
    brochure_url: Optional[str] = None
    summary: Optional[str] = None
    specs: Optional[Spec] = None
    price_range: Optional[PriceRange] = None
    variants: List[Variant] = Field(default_factory=list)
    colors: List[str] = Field(default_factory=list)
    wheels: List[str] = Field(default_factory=list)
    interiors: List[str] = Field(default_factory=list)
    packages: List[str] = Field(default_factory=list)
    accessories: List[str] = Field(default_factory=list)
    related_slugs: List[str] = Field(default_factory=list)
    published: bool = Field(True)

class Promotion(BaseModel):
    title: str
    description: Optional[str] = None
    image: Optional[str] = None
    badge: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    link: Optional[str] = None
    active: bool = Field(True)

class Dealer(BaseModel):
    name: str
    city: str
    state: Optional[str] = None
    zip: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    hours: Optional[dict] = Field(default_factory=dict)
    lat: Optional[float] = None
    lng: Optional[float] = None

class Lead(BaseModel):
    lead_type: str = Field(..., description="contact | test-drive | quote")
    name: str
    email: EmailStr
    phone: Optional[str] = None
    city: Optional[str] = None
    message: Optional[str] = None
    model_slug: Optional[str] = None
    configuration: Optional[dict] = Field(default_factory=dict)
    source: Optional[str] = None
