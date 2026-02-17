## 1. API Primitive Infrastructure Setup

- [x] 1.1 Create `/api/primitives/v1/` router directory structure with separate modules for each primitive
- [x] 1.2 Add OpenAPI specification generator to FastAPI app with `/api/primitives/v1/openapi.json` endpoint
- [x] 1.3 Implement canonical response envelope schema (data, meta, links) in `api/schemas/primitives.py`
- [x] 1.4 Add API key authentication middleware with bcrypt hashing and rate limiting (1000 req/hour default)
- [x] 1.5 Extend JWT authentication to support dual auth (API key OR JWT token) in `api/security/auth.py`
- [x] 1.6 Create feature flag system in `api/config.py` for primitive endpoint rollout control
- [x] 1.7 Add performance monitoring middleware for primitive API latency tracking (Datadog integration)
- [x] 1.8 Create primitive API test harness in `api/tests/primitives/` with contract test framework
- [x] 2.1 Extract determinism scoring logic from `api/services/determinism.py` into standalone primitive service
- [x] 2.2 Create `/api/primitives/v1/determinism/score` endpoint with POST handler
- [x] 2.3 Define OpenAPI schema for DeterminismScoreRequest and DeterminismScoreResponse with examples
- [x] 2.4 Implement request validation with Pydantic models (backtest results, thresholds, confidence intervals)
- [x] 2.5 Add determinism primitive unit tests (10+ scenarios covering edge cases)
- [x] 2.6 Add determinism primitive integration tests against live API endpoint
- [x] 2.7 Document determinism API in Markdown with code examples (Python, cURL)
- [x] 2.8 Refactor legacy workflow endpoint to call new determinism primitive internally

## 3. Gate Verification Primitive Extraction

- [x] 3.1 Extract gate verification logic from `api/routers/gates.py` into primitive service
- [x] 3.2 Create `/api/primitives/v1/gates/verify` endpoint with sync and async variants
- [x] 3.3 Define OpenAPI schema for GateVerifyRequest, GateVerifyResponse, CustomGateDefinition
- [ ] 3.4 Implement custom gate definition storage (PostgreSQL table for gate configs)
- [ ] 3.5 Add gate definition CRUD endpoints (`/api/primitives/v1/gates/definitions`)
- [x] 3.6 Integrate promotion readiness scorecard into gate verification response payload
- [ ] 3.7 Implement webhook delivery for async gate verification (POST to client URL with HMAC signature)
- [ ] 3.8 Add gate primitive tests (15+ scenarios including custom gates, async flow, webhook delivery)
- [ ] 3.9 Create certification registry table (strategy_id, gate_id, pass/fail, timestamp, score)
- [ ] 3.10 Add certification registry query endpoint (`/api/primitives/v1/gates/certifications`)

## 4. Risk and Policy Primitives

- [ ] 4.1 Extract risk validation logic into `/api/primitives/v1/risk/validate` endpoint
- [ ] 4.2 Define OpenAPI schemas for RiskValidateRequest (Sharpe, Sortino, drawdown, VaR thresholds)
- [ ] 4.3 Extract policy checking logic into `/api/primitives/v1/policy/check` endpoint
- [ ] 4.4 Define OpenAPI schemas for PolicyCheckRequest (regulatory rules, business constraints)
- [ ] 4.5 Add risk primitive tests (8+ scenarios covering threshold violations, edge cases)
- [ ] 4.6 Add policy primitive tests (8+ scenarios covering rule combinations)
- [ ] 4.7 Document risk and policy APIs with integration examples

## 5. Strategy, Evidence, and Reflexion Primitives

- [ ] 5.1 Extract strategy verification into `/api/primitives/v1/strategy/verify` endpoint
- [ ] 5.2 Extract acceptance evidence classification into `/api/primitives/v1/evidence/classify` endpoint
- [ ] 5.3 Extract reflexion feedback into `/api/primitives/v1/reflexion/suggest` endpoint
- [ ] 5.4 Define OpenAPI schemas for all three primitives with request/response examples
- [ ] 5.5 Add primitive tests for strategy, evidence, reflexion (10+ scenarios each)
- [ ] 5.6 Document all three APIs with code examples

## 6. Orchestrator Primitive

- [ ] 6.1 Design orchestrator API for multi-primitive workflow composition (`/api/primitives/v1/orchestrator/run`)
- [ ] 6.2 Implement DAG-based orchestration engine for defining primitive execution order
- [ ] 6.3 Add orchestrator workflow definition schema (JSON/YAML with primitive IDs, dependencies, conditions)
- [ ] 6.4 Implement async orchestration with progress tracking and partial result delivery
- [ ] 6.5 Add orchestrator primitive tests (12+ scenarios including error handling, retries, conditional flows)
- [ ] 6.6 Document orchestrator API with example workflows (full validation pipeline)

## 7. Promotion Readiness Primitive Refactor

- [x] 7.1 Refactor `api/services/promotion_readiness.py` to conform to primitive API standards
- [x] 7.2 Create `/api/primitives/v1/readiness/score` endpoint exposing scorecard externally
- [ ] 7.3 Ensure hard blocker logic consistency between legacy and primitive endpoints
- [ ] 7.4 Add readiness primitive tests validating API key auth, rate limits, response envelope
- [ ] 7.5 Update dashboard to call new readiness primitive (feature-flagged rollout)

## 8. Python SDK Development

- [ ] 8.1 Create `sdk/python/` project structure with `pyproject.toml` for PyPI packaging
- [ ] 8.2 Set up openapi-generator CI pipeline to auto-generate base client code from OpenAPI spec
- [ ] 8.3 Implement hand-crafted convenience layer (`aurelius.Client`) wrapping generated code
- [ ] 8.4 Add type hints to all SDK methods with Pydantic models for request/response validation
- [ ] 8.5 Implement automatic retry logic with exponential backoff (3 attempts, max 10 seconds)
- [ ] 8.6 Add response caching for GET operations (5-minute TTL with `client.cache.clear()`)
- [ ] 8.7 Implement async variants of all methods using httpx.AsyncClient
- [ ] 8.8 Create testing utilities (`MockClient`, sample fixtures) in `aurelius.testing` module
- [ ] 8.9 Write SDK unit tests (30+ scenarios covering sync/async, retries, caching, errors)
- [ ] 8.10 Write SDK integration tests against live staging API
- [ ] 8.11 Set up PyPI publishing pipeline (versioning, changelog, wheel/sdist build)
- [ ] 8.12 Write SDK documentation (README, API reference, quickstart guide)

## 9. JavaScript/TypeScript SDK Development

- [ ] 9.1 Create `sdk/javascript/` project structure with `package.json` for npm packaging
- [ ] 9.2 Generate TypeScript client from OpenAPI spec using openapi-generator
- [ ] 9.3 Implement convenience layer with type-safe interfaces (`AureliusClient`)
- [ ] 9.4 Add automatic retry logic with exponential backoff (axios-retry)
- [ ] 9.5 Implement response caching using axios-cache-adapter
- [ ] 9.6 Create React hooks for common operations (`useGateVerify`, `useReadinessScore`)
- [ ] 9.7 Add Node.js-specific utilities (webhook signature verification)
- [ ] 9.8 Write SDK unit tests with Jest (30+ scenarios)
- [ ] 9.9 Write SDK integration tests against staging API
- [ ] 9.10 Set up npm publishing pipeline with automated releases
- [ ] 9.11 Write SDK documentation with TypeScript examples

## 10. Webhook Infrastructure

- [ ] 10.1 Create webhook delivery queue using AWS SQS for async event processing
- [ ] 10.2 Implement webhook worker process that POSTs events to client URLs
- [ ] 10.3 Add HMAC signature generation for webhook payloads (SHA256 with secret key)
- [ ] 10.4 Implement exponential backoff retry logic (10 attempts over 24 hours)
- [ ] 10.5 Create dead-letter queue for failed webhook deliveries after max retries
- [ ] 10.6 Add webhook delivery dashboard in API admin panel (status, retry counts, failure logs)
- [ ] 10.7 Create webhook receiver example code (Python Flask, Node Express) with signature verification
- [ ] 10.8 Write webhook infrastructure tests (15+ scenarios including signature validation, retries)
- [ ] 10.9 Document webhook integration patterns in developer portal

## 11. Developer Portal Setup

- [ ] 11.1 Create `developer-portal/` Next.js project with TypeScript and MDX support
- [ ] 11.2 Set up Vercel deployment with preview environments for PR reviews
- [ ] 11.3 Implement authentication flow (OAuth, GitHub login) for API key management
- [ ] 11.4 Create homepage with hero section, primitive overview, and getting started CTA
- [ ] 11.5 Build API reference pages auto-generated from OpenAPI specs (Redoc integration)
- [ ] 11.6 Implement interactive API explorer with code snippet generator (Python, JS, cURL)
- [ ] 11.7 Create quickstart tutorial with step-by-step SDK installation and first API call
- [ ] 11.8 Write integration guides for common patterns (webhook receivers, async workflows, error handling)
- [ ] 11.9 Build API key management dashboard (create, view usage, revoke keys)
- [ ] 11.10 Add usage analytics visualization (requests/day, primitives used, error rates)
- [ ] 11.11 Implement certification registry public view (searchable table with filters)
- [ ] 11.12 Create certification badge generator (embeddable HTML/Markdown snippets)
- [ ] 11.13 Add full-text search with Algolia or similar (instant results, keyboard navigation)
- [ ] 11.14 Implement versioned documentation (v1, v2 dropdown with migration guides)
- [ ] 11.15 Ensure WCAG 2.1 Level AA accessibility (semantic HTML, ARIA labels, keyboard nav)
- [ ] 11.16 Optimize performance (code splitting, image optimization, CDN caching, <2s page load)

## 12. Dashboard Migration to Primitives

- [ ] 12.1 Add feature flag in dashboard config for primitive API vs legacy endpoint selection
- [ ] 12.2 Update `dashboard/src/services/api.js` to call new primitive endpoints
- [ ] 12.3 Refactor Gates.jsx to use `/api/primitives/v1/gates/verify` instead of legacy
- [ ] 12.4 Refactor Dashboard.jsx to use `/api/primitives/v1/readiness/score` for portfolio metrics
- [ ] 12.5 Update all API service methods to handle canonical response envelope (data, meta, links)
- [ ] 12.6 Add error handling for primitive API errors with user-friendly messages
- [ ] 12.7 Implement A/B test rollout: 10% dashboard traffic to primitives, monitor error rates
- [ ] 12.8 Gradually increase primitive traffic: 10% → 25% → 50% → 100% over 4 weeks
- [ ] 12.9 Add deprecation banners to legacy endpoints with sunset timeline (12 months)
- [ ] 12.10 Update dashboard tests to validate primitive API integration (28+ existing tests)

## 13. Legacy Endpoint Deprecation

- [ ] 13.1 Add `Sunset` HTTP header to legacy endpoints with deprecation date (12 months out)
- [ ] 13.2 Add `Deprecation` header and `Link` header pointing to primitive API docs
- [ ] 13.3 Update API response to include deprecation warning in body (non-breaking)
- [ ] 13.4 Create migration guide document mapping legacy endpoints to primitives
- [ ] 13.5 Set up monitoring alerts for legacy endpoint usage (track daily requests)
- [ ] 13.6 Email users still calling legacy endpoints at 6-month and 3-month milestones
- [ ] 13.7 Plan sunset ceremony: disable legacy endpoints after 12 months with final notice

## 14. Monitoring and Observability

- [ ] 14.1 Create Datadog dashboard for primitive API metrics (latency, error rate, throughput per primitive)
- [ ] 14.2 Add custom metrics for SDK usage tracking (version distribution, method calls)
- [ ] 14.3 Set up PagerDuty alerts for P0 issues (error rate >1%, p95 latency >500ms)
- [ ] 14.4 Implement distributed tracing with OpenTelemetry (trace requests across primitives)
- [ ] 14.5 Add logging for security events (authentication failures, rate limit hits, API key usage)
- [ ] 14.6 Create runbook for common primitive API incidents (outage response, rollback procedures)

## 15. Documentation and Marketing

- [ ] 15.1 Update README.md to position AURELIUS as Financial Reasoning Infrastructure
- [ ] 15.2 Create new landing page copy emphasizing API-first, composable primitives
- [ ] 15.3 Write case studies from beta partners (Interactive Brokers, QuantConnect integrations)
- [ ] 15.4 Create comparison table: AURELIUS Infrastructure vs Trading Platform competitors
- [ ] 15.5 Publish blog post series: "Building Stripe for Quants" (architecture, primitives, adoption)
- [ ] 15.6 Record video demos: Quickstart, webhook integration, custom gate definition
- [ ] 15.7 Submit talks to conferences: QCon, PyCon, FinTech DevCon
- [ ] 15.8 Launch social media campaign with #BuildWithAURELIUS hashtag

## 16. Testing and Quality Assurance

- [ ] 16.1 Achieve 90%+ code coverage for all primitive endpoints (unit + integration tests)
- [ ] 16.2 Run load tests: 1000 concurrent requests, validate p95 latency <200ms
- [ ] 16.3 Run security audit: OWASP Top 10 checklist, penetration testing for API key auth
- [ ] 16.4 Validate SDK code generation: Ensure no breaking changes when regenerating from OpenAPI
- [ ] 16.5 Beta test with 5 external partners: Collect feedback on API design, SDK ergonomics
- [ ] 16.6 Fix all P0/P1 issues identified in beta testing before public launch
- [ ] 16.7 Create contract test suite ensuring API responses match OpenAPI specs (Dredd or Schemathesis)

## 17. Launch Preparation

- [ ] 17.1 Soft launch to private beta partners (API keys pre-issued, docs access via password)
- [ ] 17.2 Public launch announcement: Publish SDKs to PyPI and npm
- [ ] 17.3 Make developer portal public at developers.aurelius.ai
- [ ] 17.4 Submit AURELIUS SDK to package manager showcases (Awesome Python, Awesome TypeScript)
- [ ] 17.5 Monitor launch metrics: API key registrations, SDK downloads, first-week error rates
- [ ] 17.6 Host "Office Hours" for developers: Weekly Q&A sessions during first month
- [ ] 17.7 Iterate on primitives based on external developer feedback (plan v2 enhancements)
