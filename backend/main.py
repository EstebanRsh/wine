from __future__ import annotations
import os
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Depends, HTTPException, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

from sqlalchemy import (
    String, Integer, Text, DateTime, Numeric, select, or_, func
)
from sqlalchemy.types import Enum as SAEnum
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# ---- Config ----
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL no está definido. Configúralo en el entorno.")

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN")  # ej. https://tu-frontend.vercel.app
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")  # opcional

# ---- DB Async ----
engine = create_async_engine(DATABASE_URL, future=True, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
Base = declarative_base()

class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    pid: Mapped[str] = mapped_column(String(24), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    winery: Mapped[Optional[str]] = mapped_column(String(120))
    varietal: Mapped[Optional[str]] = mapped_column(String(80))
    year: Mapped[Optional[int]] = mapped_column(Integer)
    photo_url: Mapped[Optional[str]] = mapped_column(Text)
    price_list: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    promo_type: Mapped[Optional[str]] = mapped_column(
        SAEnum("percent", "two_for", name="promo_type_enum"), nullable=True
    )
    promo_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    promo_valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    promo_valid_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    stock_status: Mapped[str] = mapped_column(
        SAEnum("available", "low", "out", name="stock_status_enum"),
        default="available",
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(Text)

# ---- Helpers ----

def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def is_promo_active(p: Product, when: Optional[datetime] = None) -> bool:
    when = when or now_utc()
    if p.promo_type is None:
        return False
    if p.promo_valid_from and when < p.promo_valid_from:
        return False
    if p.promo_valid_to and when > p.promo_valid_to:
        return False
    return True


def apply_promo(price_list: Decimal, promo_type: Optional[str], promo_value: Optional[Decimal]) -> Dict[str, Any]:
    """Devuelve dict con precio final y detalles; si no hay promo válida, deja final=lista."""
    if not promo_type or promo_value is None:
        return {
            "price_final": price_list,
            "promo": None,
        }
    if promo_type == "percent":
        # promo_value = porcentaje (ej. 15 => 15%)
        final = (price_list * (Decimal(100) - promo_value)) / Decimal(100)
        return {
            "price_final": final.quantize(Decimal("0.01")),
            "promo": {"type": "percent", "value": promo_value},
        }
    if promo_type == "two_for":
        # promo_value = precio total por 2 unidades
        unit = (promo_value / Decimal(2)).quantize(Decimal("0.01"))
        return {
            "price_final": unit,  # mostramos precio unitario resultante
            "promo": {"type": "two_for", "two_total": promo_value, "unit": unit},
        }
    return {
        "price_final": price_list,
        "promo": None,
    }

# ---- Schemas ----
class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, json_encoders={Decimal: lambda v: float(v)})

    pid: str
    name: str
    winery: Optional[str] = None
    varietal: Optional[str] = None
    year: Optional[int] = None
    description: Optional[str] = None
    photo_url: Optional[str] = None
    stock_status: str
    price_list: Decimal
    price_final: Decimal = Field(description="Precio final (con promo si corresponde)")
    promo_applied: Optional[Dict[str, Any]] = None

class ProductIn(BaseModel):
    name: str
    pid: str = Field(min_length=6, max_length=24)
    winery: Optional[str] = None
    varietal: Optional[str] = None
    year: Optional[int] = None
    photo_url: Optional[str] = None
    price_list: Decimal
    promo_type: Optional[str] = Field(default=None)
    promo_value: Optional[Decimal] = None
    promo_valid_from: Optional[datetime] = None
    promo_valid_to: Optional[datetime] = None
    stock_status: str = Field(default="available")
    description: Optional[str] = None

# ---- App ----
app = FastAPI(title="Wine-Pick-QR Demo", version="0.1.0")

# CORS
allow_origins = ["*"] if not FRONTEND_ORIGIN else [FRONTEND_ORIGIN]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
async def get_session() -> AsyncSession:
    async with SessionLocal() as session:
        yield session

@app.get("/health")
async def health():
    return {"status": "ok", "time": now_utc().isoformat()}

@app.get("/api/products", response_model=List[ProductOut])
async def list_products(
    q: Optional[str] = Query(None, description="Búsqueda por nombre/bodega/varietal"),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(Product)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(
                Product.name.ilike(like),
                Product.winery.ilike(like),
                Product.varietal.ilike(like),
            )
        )
    stmt = stmt.order_by(Product.name).limit(limit)
    res = await session.execute(stmt)
    items = res.scalars().all()

    out: List[ProductOut] = []
    now = now_utc()
    for p in items:
        data = apply_promo(p.price_list, p.promo_type if is_promo_active(p, now) else None, p.promo_value)
        out.append(
            ProductOut(
                pid=p.pid,
                name=p.name,
                winery=p.winery,
                varietal=p.varietal,
                year=p.year,
                description=p.description,
                photo_url=p.photo_url,
                stock_status=p.stock_status,
                price_list=p.price_list,
                price_final=data["price_final"],
                promo_applied=data["promo"],
            )
        )
    return out

@app.get("/api/products/{pid}", response_model=ProductOut)
async def get_product(pid: str, session: AsyncSession = Depends(get_session)):
    res = await session.execute(select(Product).where(Product.pid == pid))
    p = res.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    data = apply_promo(p.price_list, p.promo_type if is_promo_active(p) else None, p.promo_value)
    return ProductOut(
        pid=p.pid,
        name=p.name,
        winery=p.winery,
        varietal=p.varietal,
        year=p.year,
        description=p.description,
        photo_url=p.photo_url,
        stock_status=p.stock_status,
        price_list=p.price_list,
        price_final=data["price_final"],
        promo_applied=data["promo"],
    )

@app.post("/api/admin/products", response_model=ProductOut)
async def create_product(
    payload: ProductIn,
    session: AsyncSession = Depends(get_session),
    x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
):
    if not ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="ADMIN_TOKEN no configurado en el backend")
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Token inválido")

    # Verifica PID único
    exists = await session.execute(select(func.count()).select_from(Product).where(Product.pid == payload.pid))
    if exists.scalar_one() > 0:
        raise HTTPException(status_code=409, detail="PID ya existe")

    p = Product(
        pid=payload.pid,
        name=payload.name,
        winery=payload.winery,
        varietal=payload.varietal,
        year=payload.year,
        photo_url=payload.photo_url,
        price_list=payload.price_list,
        promo_type=payload.promo_type,
        promo_value=payload.promo_value,
        promo_valid_from=payload.promo_valid_from,
        promo_valid_to=payload.promo_valid_to,
        stock_status=payload.stock_status,
        description=payload.description,
    )
    session.add(p)
    await session.commit()

    data = apply_promo(p.price_list, p.promo_type if is_promo_active(p) else None, p.promo_value)
    return ProductOut(
        pid=p.pid,
        name=p.name,
        winery=p.winery,
        varietal=p.varietal,
        year=p.year,
        description=p.description,
        photo_url=p.photo_url,
        stock_status=p.stock_status,
        price_list=p.price_list,
        price_final=data["price_final"],
        promo_applied=data["promo"],
    )

# Nota: Uvicorn se lanza desde el proceso del host (Render). No incluyas if __name__ == "__main__".
