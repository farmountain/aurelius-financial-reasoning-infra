"""
Readiness Primitive API Endpoint

Standalone promotion readiness scoring endpoint.
Exposes DROPS (Determinism, Risk, Policy, Ops, User) scorecard externally.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Tuple, Optional, Dict, Any
from pydantic import BaseModel, Field
from schemas.primitives import create_canonical_response, create_error_response, ErrorCode
from services.promotion_readiness import (
    build_readiness_payload,
    ReadinessSignals
)
from security.dual_auth import get_authenticated_user
from primitives.feature_flags import FeatureFlags

router = APIRouter(prefix="/readiness", tags=["readiness"])


class ReadinessScoreRequest(BaseModel):
    """Request for readiness scoring."""
    strategy_id: str
    signals: Dict[str, Any] = Field(..., description="Readiness signals from various checks")
    
    class Config:
        json_schema_extra = {
            "example": {
                "strategy_id": "strat-123",
                "signals": {
                    "run_identity_present": True,
                    "parity_checked": True,
                    "parity_passed": True,
                    "validation_passed": True,
                    "crv_available": True,
                    "risk_metrics_complete": True,
                    "policy_block_reasons": [],
                    "lineage_complete": True,
                    "startup_status": "healthy",
                    "startup_reasons": [],
                    "evidence_stale": False,
                    "environment_caveat": None,
                    "evidence_classification": "GREEN"
                }
            }
        }


class ReadinessScoreResponse(BaseModel):
    """Readiness scoring result."""
    strategy_id: str
    overall_score: float = Field(..., description="Overall readiness score (0-100)")
    color: str = Field(..., description="Traffic light: GREEN, AMBER, RED")
    recommendation: str
    dimensions: Dict[str, float] = Field(..., description="DROPS dimension scores")
    blockers: list[str] = Field(default_factory=list, description="Hard blockers preventing promotion")
    
    class Config:
        json_schema_extra = {
            "example": {
                "strategy_id": "strat-123",
                "overall_score": 92.5,
                "color": "GREEN",
                "recommendation": "Strategy ready for promotion",
                "dimensions": {
                    "D": 100.0,
                    "R": 95.0,
                    "O": 100.0,
                    "P": 85.0,
                    "S": 80.0
                },
                "blockers": []
            }
        }


@router.post("/score", response_model=dict)
async def score_readiness(
    request: ReadinessScoreRequest,
    auth: Tuple = Depends(get_authenticated_user)
):
    """
    Score promotion readiness for a strategy.
    
    Computes DROPS scorecard (Determinism, Risk, Policy, Ops, User) from
    various verification signals to determine promotion readiness.
    
    **Authentication:** Requires API key (X-API-Key) or JWT token (Authorization: Bearer)
    
    **Rate Limits:**
    - API key: 1000 requests/hour
    - JWT token: 5000 requests/hour
    
    **DROPS Dimensions:**
    - **D**eterminism: Backtest reproducibility and parity
    - **R**isk: CRV metrics within thresholds
    - **O**ps: Operational readiness (health, lineage)
    - **P**olicy: Governance and compliance checks
    - **S**tability: Validation and acceptance evidence
    
    **Request:**
    - `strategy_id`: Strategy identifier
    - `signals`: Dictionary of readiness signals from various checks
    
    **Response:**
    - `overall_score`: Weighted score 0-100
    - `color`: GREEN (>=85), AMBER (70-84), RED (<70)
    - `recommendation`: Human-readable promotion decision
    - `dimensions`: Individual DROPS scores
    - `blockers`: List of hard blockers if any
    
    **Example:**
    ```python
    import requests
    
    response = requests.post(
        "https://api.aurelius.ai/api/primitives/v1/readiness/score",
        headers={"X-API-Key": "your_api_key"},
        json={
            "strategy_id": "momentum-v2",
            "signals": {
                "run_identity_present": True,
                "parity_checked": True,
                "parity_passed": True,
                "validation_passed": True,
                "crv_available": True,
                "risk_metrics_complete": True,
                "policy_block_reasons": [],
                "lineage_complete": True,
                "startup_status": "healthy",
                "startup_reasons": [],
                "evidence_stale": False,
                "environment_caveat": None,
                "evidence_classification": "GREEN"
            }
        }
    )
    
    result = response.json()
    if result["data"]["color"] == "GREEN":
        print(f"Ready for promotion! Score: {result['data']['overall_score']}")
    else:
        print(f"Blockers: {result['data']['blockers']}")
    ```
    """
    # Check feature flag
    FeatureFlags.check_primitive_enabled("readiness")
    
    user_id, auth_method, rate_limit_headers = auth
    
    try:
        # Convert signals dict to ReadinessSignals object
        signals = ReadinessSignals(**request.signals)
        
        # Build readiness payload
        payload = build_readiness_payload(signals)
        
        # Extract response fields
        response_data = ReadinessScoreResponse(
            strategy_id=request.strategy_id,
            overall_score=payload["overall_score"],
            color=payload["color"],
            recommendation=payload["recommendation"],
            dimensions=payload["dimensions"],
            blockers=payload.get("blockers", [])
        )
        
        # Build canonical response
        response = create_canonical_response(
            data=response_data.dict(),
            links={
                "self": f"/api/primitives/v1/readiness/score",
                "docs": "/api/primitives/openapi/v1.json",
                "strategy": f"/api/v1/strategies/{request.strategy_id}"
            }
        )
        
        # Add rate limit headers
        for key, value in rate_limit_headers.items():
            response.setdefault("headers", {})[key] = value
        
        return response
        
    except TypeError as e:
        # Missing or invalid signals fields
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_error_response(
                ErrorCode.VALIDATION_ERROR,
                f"Invalid signals format: {str(e)}"
            )
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_error_response(
                ErrorCode.INTERNAL_ERROR,
                f"Readiness scoring failed: {str(e)}"
            )
        )


@router.get("/health", response_model=dict)
async def readiness_health():
    """
    Health check endpoint for readiness primitive.
    
    Returns service health status.
    """
    return {"status": "ok"}
