from fastapi import APIRouter
from backend.app.api.v1.endpoints import (
    auth,
    health,
    resources,
    optimization,
    timetable,
    analytics,
    validation,
    rescheduling
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication & Security"])
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(resources.router, prefix="/resources", tags=["Resource Management"])
api_router.include_router(optimization.router, prefix="/optimize", tags=["Optimization Engines"])
api_router.include_router(timetable.router, prefix="/timetable", tags=["Timetable Management"])
api_router.include_router(timetable.router, prefix="/timetables", tags=["Timetable Management (Alias)"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Timetable Analytics"])
api_router.include_router(validation.router, prefix="/validation", tags=["Constraint Validation"])
api_router.include_router(rescheduling.router, prefix="/rescheduling", tags=["What-If Rescheduling"])
