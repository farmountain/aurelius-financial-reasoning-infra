"""
OpenAPI specification endpoints for AURELIUS primitives.

Provides machine-readable API documentation for SDK generation and
interactive API explorer integration.
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from typing import Dict, Any

router = APIRouter(prefix="/openapi", tags=["openapi"])


def generate_primitives_openapi_spec() -> Dict[str, Any]:
    """
    Generate OpenAPI 3.0 specification for AURELIUS API primitives.
    
    Returns comprehensive API documentation including:
    - All primitive endpoints with request/response schemas
    - Authentication requirements (API key, JWT)
    - Error codes and canonical response envelope
    - Rate limiting policies
    """
    spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "AURELIUS Financial Reasoning Infrastructure API",
            "version": "1.0.0",
            "description": "Composable primitives for financial reasoning verification. "
                           "Integrate determinism scoring, risk validation, policy checking, "
                           "and gate verification into your quantitative workflows.",
            "contact": {
                "name": "AURELIUS API Support",
                "url": "https://developers.aurelius.ai",
                "email": "api@aurelius.ai"
            },
            "license": {
                "name": "MIT",
                "url": "https://opensource.org/licenses/MIT"
            }
        },
        "servers": [
            {
                "url": "https://api.aurelius.ai",
                "description": "Production"
            },
            {
                "url": "https://staging.api.aurelius.ai",
                "description": "Staging"
            },
            {
                "url": "http://localhost:8000",
                "description": "Local development"
            }
        ],
        "paths": {
            "/api/primitives/v1/determinism/score": {
                "post": {
                    "tags": ["determinism"],
                    "summary": "Score determinism of backtest results",
                    "description": "Analyzes variance in key metrics across multiple backtest runs to detect non-deterministic behavior. "
                                   "A score of 100 indicates perfect determinism. Scores below 95 typically indicate bugs or data issues.",
                    "operationId": "score_determinism",
                    "security": [
                        {"ApiKeyAuth": []},
                        {"BearerAuth": []}
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/DeterminismScoreRequest"},
                                "example": {
                                    "strategy_id": "strat-123",
                                    "runs": [
                                        {
                                            "run_id": "run-1",
                                            "timestamp": "2026-02-16T10:00:00Z",
                                            "total_return": 0.15,
                                            "sharpe_ratio": 1.8,
                                            "max_drawdown": 0.12,
                                            "trade_count": 42,
                                            "final_portfolio_value": 115000.0,
                                            "execution_time_ms": 1250
                                        },
                                        {
                                            "run_id": "run-2",
                                            "timestamp": "2026-02-16T10:05:00Z",
                                            "total_return": 0.15,
                                            "sharpe_ratio": 1.8,
                                            "max_drawdown": 0.12,
                                            "trade_count": 42,
                                            "final_portfolio_value": 115000.0,
                                            "execution_time_ms": 1230
                                        }
                                    ],
                                    "threshold": 95.0
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Determinism scoring completed successfully",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/CanonicalEnvelope"},
                                    "example": {
                                        "data": {
                                            "score": 98.5,
                                            "passed": True,
                                            "confidence_interval": 0.95,
                                            "p_value": 0.001,
                                            "variance_metrics": {
                                                "total_return": 0.0,
                                                "sharpe_ratio": 0.0,
                                                "max_drawdown": 0.0,
                                                "trade_count": 0.0
                                            },
                                            "issues": []
                                        },
                                        "meta": {
                                            "version": "v1",
                                            "timestamp": "2026-02-17T14:30:00Z",
                                            "request_id": "req-abc123"
                                        },
                                        "links": {
                                            "self": "/api/primitives/v1/determinism/score",
                                            "docs": "/api/primitives/openapi/v1.json"
                                        }
                                    }
                                }
                            },
                            "headers": {
                                "X-RateLimit-Limit": {
                                    "schema": {"type": "integer"},
                                    "description": "Request limit per hour"
                                },
                                "X-RateLimit-Remaining": {
                                    "schema": {"type": "integer"},
                                    "description": "Remaining requests in window"
                                },
                                "X-RateLimit-Reset": {
                                    "schema": {"type": "integer"},
                                    "description": "Unix timestamp when limit resets"
                                }
                            }
                        },
                        "400": {
                            "description": "Invalid request (fewer than 2 runs, invalid threshold)",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        },
                        "401": {"$ref": "#/components/responses/Unauthorized"},
                        "429": {"$ref": "#/components/responses/RateLimitExceeded"},
                        "503": {
                            "description": "Primitive disabled via feature flag",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        }
                    }
                }
            },
            "/api/primitives/v1/determinism/health": {
                "get": {
                    "tags": ["determinism"],
                    "summary": "Check determinism primitive health",
                    "description": "Health check endpoint for monitoring",
                    "operationId": "determinism_health",
                    "responses": {
                        "200": {
                            "description": "Primitive is healthy",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {"type": "string", "example": "ok"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "CanonicalEnvelope": {
                    "type": "object",
                    "description": "Standard response envelope for all primitive APIs",
                    "properties": {
                        "data": {
                            "type": "object",
                            "description": "Response payload specific to the endpoint"
                        },
                        "meta": {
                            "type": "object",
                            "properties": {
                                "version": {"type": "string", "example": "v1"},
                                "timestamp": {"type": "string", "format": "date-time"},
                                "request_id": {"type": "string", "format": "uuid"}
                            }
                        },
                        "links": {
                            "type": "object",
                            "description": "HATEOAS links to related resources",
                            "additionalProperties": {"type": "string", "format": "uri"}
                        }
                    },
                    "required": ["data", "meta"]
                },
                "ErrorResponse": {
                    "type": "object",
                    "properties": {
                        "error": {
                            "type": "object",
                            "properties": {
                                "code": {"type": "string", "example": "VALIDATION_ERROR"},
                                "message": {"type": "string"},
                                "details": {"type": "object"}
                            },
                            "required": ["code", "message"]
                        },
                        "meta": {
                            "type": "object",
                            "properties": {
                                "timestamp": {"type": "string", "format": "date-time"},
                                "request_id": {"type": "string", "format": "uuid"}
                            }
                        }
                    },
                    "required": ["error", "meta"]
                },
                "BacktestRun": {
                    "type": "object",
                    "description": "Single backtest run result",
                    "properties": {
                        "run_id": {"type": "string", "example": "run-1"},
                        "timestamp": {"type": "string", "format": "date-time", "example": "2026-02-16T10:00:00Z"},
                        "total_return": {"type": "number", "format": "float", "example": 0.15},
                        "sharpe_ratio": {"type": "number", "format": "float", "example": 1.8},
                        "max_drawdown": {"type": "number", "format": "float", "example": 0.12},
                        "trade_count": {"type": "integer", "example": 42},
                        "final_portfolio_value": {"type": "number", "format": "float", "example": 115000.0},
                        "execution_time_ms": {"type": "number", "format": "float", "example": 1250}
                    },
                    "required": ["run_id", "timestamp", "total_return", "sharpe_ratio", "max_drawdown", "trade_count", "final_portfolio_value", "execution_time_ms"]
                },
                "DeterminismScoreRequest": {
                    "type": "object",
                    "description": "Request for determinism scoring of backtest results",
                    "properties": {
                        "strategy_id": {"type": "string", "example": "strat-123"},
                        "runs": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/BacktestRun"},
                            "minItems": 2,
                            "description": "At least 2 runs required for comparison"
                        },
                        "threshold": {
                            "type": "number",
                            "format": "float",
                            "default": 95.0,
                            "minimum": 0,
                            "maximum": 100,
                            "example": 95.0,
                            "description": "Minimum score to pass (0-100)"
                        }
                    },
                    "required": ["strategy_id", "runs"]
                },
                "DeterminismScoreResponse": {
                    "type": "object",
                    "description": "Determinism scoring result",
                    "properties": {
                        "score": {
                            "type": "number",
                            "format": "float",
                            "minimum": 0,
                            "maximum": 100,
                            "example": 98.5,
                            "description": "Determinism score (0-100, 100=perfect)"
                        },
                        "passed": {"type": "boolean", "example": true, "description": "Whether score meets threshold"},
                        "confidence_interval": {"type": "number", "format": "float", "example": 0.95, "description": "Statistical confidence (0-1)"},
                        "p_value": {"type": "number", "format": "float", "example": 0.001, "description": "Statistical significance"},
                        "variance_metrics": {
                            "type": "object",
                            "description": "Variance across runs for each metric",
                            "properties": {
                                "total_return": {"type": "number", "format": "float", "example": 0.0},
                                "sharpe_ratio": {"type": "number", "format": "float", "example": 0.0},
                                "max_drawdown": {"type": "number", "format": "float", "example": 0.0},
                                "trade_count": {"type": "number", "format": "float", "example": 0.0}
                            }
                        },
                        "issues": {
                            "type": "array",
                            "items": {"type": "string"},
                            "example": [],
                            "description": "Detected non-deterministic behaviors"
                        }
                    },
                    "required": ["score", "passed", "confidence_interval", "p_value", "variance_metrics", "issues"]
                }
            },
            "securitySchemes": {
                "ApiKeyAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-Key",
                    "description": "API key for external developers (1000 requests/hour)"
                },
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": "JWT token for authenticated users (5000 requests/hour)"
                }
            },
            "responses": {
                "Unauthorized": {
                    "description": "Authentication credentials missing or invalid",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                        }
                    }
                },
                "Forbidden": {
                    "description": "Insufficient permissions for requested operation",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                        }
                    }
                },
                "NotFound": {
                    "description": "Resource not found",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                        }
                    }
                },
                "RateLimitExceeded": {
                    "description": "Rate limit exceeded",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                        }
                    },
                    "headers": {
                        "X-RateLimit-Limit": {
                            "schema": {"type": "integer"},
                            "description": "Total request limit per hour"
                        },
                        "X-RateLimit-Remaining": {
                            "schema": {"type": "integer"},
                            "description": "Remaining requests in current window"
                        },
                        "X-RateLimit-Reset": {
                            "schema": {"type": "integer"},
                            "description": "Unix timestamp when limit resets"
                        }
                    }
                }
            }
        },
        "tags": [
            {
                "name": "determinism",
                "description": "Determinism scoring for backtest result consistency"
            },
            {
                "name": "risk",
                "description": "Risk validation for portfolio metrics"
            },
            {
                "name": "policy",
                "description": "Policy compliance checking"
            },
            {
                "name": "strategy",
                "description": "Strategy verification and validation"
            },
            {
                "name": "evidence",
                "description": "Acceptance evidence classification"
            },
            {
                "name": "gates",
                "description": "Gate verification and certification registry"
            },
            {
                "name": "reflexion",
                "description": "Reflexion feedback for strategy improvement"
            },
            {
                "name": "orchestrator",
                "description": "Multi-primitive workflow orchestration"
            },
            {
                "name": "readiness",
                "description": "Promotion readiness scorecard"
            }
        ]
    }
    
    return spec


@router.get("/primitives/v1.json", response_class=JSONResponse)
async def get_primitives_openapi_spec():
    """
    Get OpenAPI 3.0 specification for AURELIUS API primitives.
    
    This endpoint provides a machine-readable API specification that can be used for:
    - SDK code generation (openapi-generator, swagger-codegen)
    - Interactive API documentation (Swagger UI, Redoc)
    - Contract testing (Dredd, Schemathesis)
    - API client tools (Postman, Insomnia)
    
    The specification follows OpenAPI 3.0 standard and includes all primitive
    endpoints with complete request/response schemas, authentication requirements,
    and error codes.
    """
    spec = generate_primitives_openapi_spec()
    return JSONResponse(content=spec)


@router.get("/primitives/v1.yaml")
async def get_primitives_openapi_spec_yaml():
    """
    Get OpenAPI 3.0 specification in YAML format.
    
    Same as JSON endpoint but returns YAML for better human readability.
    """
    import yaml
    spec = generate_primitives_openapi_spec()
    yaml_content = yaml.dump(spec, default_flow_style=False, sort_keys=False)
    return JSONResponse(content=yaml_content, media_type="application/x-yaml")
