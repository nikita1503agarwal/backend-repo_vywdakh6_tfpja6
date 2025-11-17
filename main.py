import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import db, create_document, get_documents
from schemas import CarModel, Promotion, Dealer, Lead

app = FastAPI(title="Aurora Motors API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Aurora Motors API running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = getattr(db, 'name', None) or ("✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set")
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["connection_status"] = "Connected"
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response

# Seed defaults endpoint (optional helper for demo content)
class SeedResult(BaseModel):
    inserted: int

@app.post("/seed", response_model=SeedResult)
def seed_demo_content():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    # Only seed if empty
    existing_models = db["carmodel"].count_documents({})
    inserted = 0
    if existing_models == 0:
        demo_models = [
            CarModel(
                name="Aurora Flux",
                slug="aurora-flux",
                body_type="Sedan",
                fuel_type="EV",
                summary="A sleek electric sedan blending performance and efficiency.",
                price_range={"min": 39999, "max": 55999, "currency": "USD"},
                hero_image="/assets/flux-hero.jpg",
                gallery=[{"url": "/assets/flux-1.jpg", "type": "image"}],
                variants=[
                    {"name": "Standard", "engine": "Dual Motor", "transmission": "Single Speed", "drivetrain": "AWD", "price": 39999},
                    {"name": "Performance", "engine": "Tri-Motor", "transmission": "Single Speed", "drivetrain": "AWD", "price": 52999},
                ],
                colors=["Onyx Black", "Glacier White", "Crimson Red"],
                wheels=["18\" Aero", "20\" Sport"],
                interiors=["Black Tech", "Stone Grey"],
                packages=["Pilot Assist", "Premium Sound"],
                accessories=["Roof Rack", "All-Weather Mats"],
                related_slugs=[],
                published=True,
            ),
            CarModel(
                name="Aurora Trail", slug="aurora-trail", body_type="SUV", fuel_type="Hybrid",
                summary="Versatile hybrid SUV ready for the city or the wild.",
                price_range={"min": 32999, "max": 44999, "currency": "USD"},
                hero_image="/assets/trail-hero.jpg",
                gallery=[{"url": "/assets/trail-1.jpg", "type": "image"}],
                variants=[
                    {"name": "Eco", "engine": "1.6L Hybrid", "transmission": "CVT", "drivetrain": "FWD", "price": 32999},
                    {"name": "Adventure", "engine": "2.0L Hybrid", "transmission": "CVT", "drivetrain": "AWD", "price": 41999},
                ],
                colors=["Forest Green", "Canyon Sand", "Glacier White"],
                wheels=["17\" Terrain", "19\" Premium"],
                interiors=["Charcoal", "Saddle"],
                packages=["Tow Pack", "Terrain Pro"],
                accessories=["Cargo Liner", "Cross Bars"],
                related_slugs=["aurora-flux"],
                published=True,
            ),
        ]
        for m in demo_models:
            create_document("carmodel", m)
            inserted += 1

    existing_promos = db["promotion"].count_documents({})
    if existing_promos == 0:
        promos = [
            Promotion(title="0.99% APR for 36 months", description="Limited-time financing on select models.", active=True),
            Promotion(title="Year-End Event", description="Save up to $2,500 on in-stock vehicles.", active=True),
        ]
        for p in promos:
            create_document("promotion", p)
            inserted += 1

    return {"inserted": inserted}

# Public API endpoints

@app.get("/models", response_model=List[CarModel])
def list_models(body_type: Optional[str] = None, fuel_type: Optional[str] = None):
    if db is None:
        return []
    filter_query = {"published": True}
    if body_type:
        filter_query["body_type"] = body_type
    if fuel_type:
        filter_query["fuel_type"] = fuel_type
    docs = get_documents("carmodel", filter_query)
    # coerce _id away and pydantic parsing
    results: List[CarModel] = []
    for d in docs:
        d.pop("_id", None)
        results.append(CarModel(**d))
    return results

@app.get("/models/{slug}", response_model=CarModel)
def get_model(slug: str):
    if db is None:
        raise HTTPException(status_code=404, detail="Not found")
    docs = get_documents("carmodel", {"slug": slug, "published": True}, limit=1)
    if not docs:
        raise HTTPException(status_code=404, detail="Model not found")
    d = docs[0]
    d.pop("_id", None)
    return CarModel(**d)

@app.get("/promotions", response_model=List[Promotion])
def get_promotions():
    if db is None:
        return []
    docs = get_documents("promotion", {"active": True})
    for d in docs:
        d.pop("_id", None)
    return [Promotion(**d) for d in docs]

@app.get("/dealers", response_model=List[Dealer])
def list_dealers(city: Optional[str] = None, zip: Optional[str] = None):
    if db is None:
        return []
    q = {}
    if city:
        q["city"] = {"$regex": city, "$options": "i"}
    if zip:
        q["zip"] = zip
    docs = get_documents("dealer", q)
    for d in docs:
        d.pop("_id", None)
    return [Dealer(**d) for d in docs]

# Lead capture endpoints with validation

@app.post("/leads", status_code=201)
def create_lead(lead: Lead):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    lead_id = create_document("lead", lead)
    return {"id": lead_id, "status": "received"}

# Configurator price calculation helper (stateless)
class ConfigSelection(BaseModel):
    model_slug: str
    variant: Optional[str] = None
    color: Optional[str] = None
    wheels: Optional[str] = None
    interior: Optional[str] = None
    packages: Optional[List[str]] = None
    accessories: Optional[List[str]] = None

@app.post("/config/price")
def calculate_price(sel: ConfigSelection):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    docs = get_documents("carmodel", {"slug": sel.model_slug}, limit=1)
    if not docs:
        raise HTTPException(status_code=404, detail="Model not found")
    model = docs[0]
    base = 0.0
    # variant base price
    if sel.variant:
        for v in model.get("variants", []):
            if v.get("name") == sel.variant:
                base = float(v.get("price", 0))
                break
    if base == 0 and model.get("price_range"):
        base = float(model["price_range"].get("min", 0))

    # simple option pricing rules (demo)
    extras = 0.0
    if sel.color:
        extras += 500 if "Pearl" in sel.color or "Metallic" in sel.color else 0
    if sel.wheels:
        extras += 1200 if "20" in sel.wheels or "19" in sel.wheels else 0
    if sel.interior:
        extras += 800 if "Leather" in sel.interior else 0
    if sel.packages:
        extras += 1500 * len(sel.packages)
    if sel.accessories:
        extras += 200 * len(sel.accessories)

    total = base + extras
    return {"base": base, "extras": extras, "total": total}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
