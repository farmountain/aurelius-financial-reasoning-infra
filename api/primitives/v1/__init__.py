"""
AURELIUS API Primitives v1

RESTful infrastructure primitives for financial reasoning verification.
Provides standalone endpoints for:
- Determinism scoring
- Risk validation
- Policy checking
- Strategy verification
- Evidence classification
- Gate verification
- Reflexion feedback
- Orchestration composition
"""
from fastapi import APIRouter

# Main router for all v1 primitives
router = APIRouter(prefix="/api/primitives/v1", tags=["primitives-v1"])

# OpenAPI specification endpoint
from .openapi import router as openapi_router
router.include_router(openapi_router)

# Individual primitive routers
from .determinism import router as determinism_router
router.include_router(determinism_router)

from .gates import router as gates_router
router.include_router(gates_router)

# from .risk import router as risk_router
# from .policy import router as policy_router
# from .strategy import router as strategy_router
# from .evidence import router as evidence_router
# from .reflexion import router as reflexion_router
# from .orchestrator import router as orchestrator_router
# from .readiness import router as readiness_router

# router.include_router(risk_router)
# router.include_router(policy_router)
# router.include_router(strategy_router)
# router.include_router(evidence_router)
# router.include_router(reflexion_router)
# router.include_router(orchestrator_router)
# router.include_router(readiness_router)

__all__ = ["router"]
