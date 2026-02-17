"""
Gates Primitive API Endpoint

Standalone gate verification endpoint for strategy promotion gates.
Supports dev, CRV, and product gates with sync verification.
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import Tuple
from schemas.primitives import create_canonical_response, create_error_response, ErrorCode
from services.gate_verification import (
    GateVerificationService,
    GateVerifyRequest,
    GateVerifyResponse
)
from security.dual_auth import get_authenticated_user
from primitives.feature_flags import FeatureFlags

router = APIRouter(prefix="/gates", tags=["gates"])


@router.post("/verify", response_model=dict)
async def verify_gate(
    request: GateVerifyRequest,
    auth: Tuple = Depends(get_authenticated_user)
):
    """
    Verify strategy against gate requirements.
    
    Performs gate verification checks to determine if a strategy meets
    promotion requirements (dev → CRV → product).
    
    **Authentication:** Requires API key (X-API-Key) or JWT token (Authorization: Bearer)
    
    **Rate Limits:**
    - API key: 1000 requests/hour
    - JWT token: 5000 requests/hour
    
    **Gate Types:**
    - `dev`: Development gate (strategy exists, backtest complete, determinism)
    - `crv`: CRV gate (Sharpe ratio, drawdown, return thresholds)
    - `product`: Product gate (all dev + CRV + validation)
    
    **Request:**
    - `strategy_id`: Strategy identifier
    - `gate_type`: Type of gate to verify (dev, crv, product)
    - `backtest_metrics`: Backtest results for verification
    - `validation_metrics`: Walk-forward validation results (product gate only)
    - `thresholds`: Custom thresholds (optional, uses defaults if not provided)
    
    **Response:**
    - `passed`: Whether strategy passed all checks
    - `gate_status`: passed, failed, or blocked
    - `checks`: List of individual check results
    - `score`: Overall gate score (0-100)
    - `recommendations`: Improvement suggestions if failed
    
    **Example:**
    ```python
    import requests
    
    response = requests.post(
        "https://api.aurelius.ai/api/primitives/v1/gates/verify",
        headers={"X-API-Key": "your_api_key"},
        json={
            "strategy_id": "strat-123",
            "gate_type": "dev",
            "backtest_metrics": {
                "run_identity": "run-abc",
                "sharpe_ratio": 1.8,
                "max_drawdown": 0.12,
                "total_return": 0.15,
                "replay_pass": True
            }
        }
    )
    
    result = response.json()
    if result["data"]["passed"]:
        print("Gate passed!")
    else:
        print("Recommendations:", result["data"]["recommendations"])
    ```
    """
    # Check feature flag
    FeatureFlags.check_primitive_enabled("gates")
    
    user_id, auth_method, rate_limit_headers = auth
    
    try:
        # Verify gate
        result = GateVerificationService.verify_gate(request)
        
        # Build canonical response
        response = create_canonical_response(
            data=result.dict(),
            links={
                "self": f"/api/primitives/v1/gates/verify",
                "docs": "/api/primitives/openapi/v1.json",
                "strategy": f"/api/v1/strategies/{request.strategy_id}"
            }
        )
        
        # Add rate limit headers
        for key, value in rate_limit_headers.items():
            response.setdefault("headers", {})[key] = value
        
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_error_response(
                ErrorCode.VALIDATION_ERROR,
                str(e)
            )
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_error_response(
                ErrorCode.INTERNAL_ERROR,
                f"Gate verification failed: {str(e)}"
            )
        )


@router.post("/verify/async", response_model=dict)
async def verify_gate_async(
    request: GateVerifyRequest,
    background_tasks: BackgroundTasks,
    auth: Tuple = Depends(get_authenticated_user)
):
    """
    Verify strategy against gate requirements (async variant).
    
    Initiates gate verification in the background and returns immediately.
    Result will be delivered via webhook (if configured) or can be polled.
    
    **Authentication:** Requires API key (X-API-Key) or JWT token (Authorization: Bearer)
    
    **Rate Limits:**
    - API key: 1000 requests/hour
    - JWT token: 5000 requests/hour
    
    **Request:**
    Same as `/verify` endpoint
    
    **Response:**
    - `verification_id`: Unique ID for tracking this verification
    - `status`: Status of the verification (pending, in_progress, completed, failed)
    - `poll_url`: URL to check verification status
    
    **Example:**
    ```python
    import requests
    
    response = requests.post(
        "https://api.aurelius.ai/api/primitives/v1/gates/verify/async",
        headers={"X-API-Key": "your_api_key"},
        json={
            "strategy_id": "strat-123",
            "gate_type": "product",
            "backtest_metrics": {...},
            "validation_metrics": {...}
        }
    )
    
    result = response.json()
    verification_id = result["data"]["verification_id"]
    
    # Poll for results
    status_response = requests.get(
        f"https://api.aurelius.ai/api/primitives/v1/gates/verify/{verification_id}",
        headers={"X-API-Key": "your_api_key"}
    )
    ```
    """
    # Check feature flag
    FeatureFlags.check_primitive_enabled("gates")
    
    user_id, auth_method, rate_limit_headers = auth
    
    # Generate verification ID
    import uuid
    verification_id = f"verify-{uuid.uuid4().hex[:12]}"
    
    # Schedule background task
    def run_verification():
        """Background task to run gate verification."""
        try:
            result = GateVerificationService.verify_gate(request)
            # TODO: Store result in database
            # TODO: Trigger webhook if configured
            return result
        except Exception as e:
            # TODO: Log error and update status
            pass
    
    background_tasks.add_task(run_verification)
    
    # Return immediate response
    response = create_canonical_response(
        data={
            "verification_id": verification_id,
            "status": "pending",
            "poll_url": f"/api/primitives/v1/gates/verify/{verification_id}"
        },
        links={
            "self": f"/api/primitives/v1/gates/verify/async",
            "status": f"/api/primitives/v1/gates/verify/{verification_id}",
            "docs": "/api/primitives/openapi/v1.json"
        }
    )
    
    # Add rate limit headers
    for key, value in rate_limit_headers.items():
        response.setdefault("headers", {})[key] = value
    
    return response


@router.get("/health", response_model=dict)
async def gates_health():
    """
    Health check endpoint for gates primitive.
    
    Returns service health status.
    """
    return {"status": "ok"}
