"""MediSetu FastAPI application entrypoint."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.consultations import router as consultations_router
from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.api.laboratory import router as laboratory_router
from app.api.billing import router as billing_router
from app.api.inventory import router as inventory_router
from app.api.alerts import router as alerts_router
from app.api.medicines import router as medicines_router
from app.api.patients import router as patients_router
from app.api.pharmacy import router as pharmacy_router
from app.api.prescriptions import router as prescriptions_router
from app.api.referrals import router as referrals_router
from app.api.timeline import router as timeline_router
from app.api.users import router as users_router
from app.core.config import get_settings
from app.core.error_handlers import register_exception_handlers
from app.core.logging_config import configure_logging

configure_logging()
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("MediSetu backend starting (environment=%s)", settings.ENVIRONMENT)
    yield
    logger.info("MediSetu backend shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-assisted pre-consultation and clinical workflow platform (prototype).",
    version="1.0.0",
    lifespan=lifespan,
)
register_exception_handlers(app)

app.include_router(health_router)
app.include_router(health_router, prefix=settings.API_V1_PREFIX)
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(users_router, prefix=settings.API_V1_PREFIX)
app.include_router(patients_router, prefix=settings.API_V1_PREFIX)
app.include_router(consultations_router, prefix=settings.API_V1_PREFIX + "/consultations")
app.include_router(prescriptions_router, prefix=settings.API_V1_PREFIX + "/prescriptions", tags=["prescriptions"])
app.include_router(referrals_router, prefix=settings.API_V1_PREFIX + "/referrals", tags=["referrals"])
app.include_router(medicines_router, prefix=settings.API_V1_PREFIX + "/medicines", tags=["medicines"])
app.include_router(documents_router, prefix=settings.API_V1_PREFIX + "/documents", tags=["documents"])
app.include_router(pharmacy_router, prefix=settings.API_V1_PREFIX + "/pharmacy", tags=["pharmacy"])
app.include_router(timeline_router, prefix=settings.API_V1_PREFIX + "/timeline", tags=["timeline"])

app.include_router(laboratory_router, prefix=settings.API_V1_PREFIX + "/laboratory", tags=["laboratory"])
app.include_router(billing_router, prefix=settings.API_V1_PREFIX + "/billing", tags=["billing"])
app.include_router(inventory_router, prefix=settings.API_V1_PREFIX + "/inventory", tags=["inventory"])
app.include_router(alerts_router, prefix=settings.API_V1_PREFIX + "/alerts", tags=["alerts"])
