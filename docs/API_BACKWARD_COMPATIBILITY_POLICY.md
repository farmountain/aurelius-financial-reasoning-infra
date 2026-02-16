# API Backward Compatibility Policy

## Scope

This policy applies to HTTP endpoints exposed by the AURELIUS API and consumed by first-party clients (dashboard) and external integrations.

## Compatibility Levels

- **Non-breaking**
  - Adding optional request fields.
  - Adding new response fields.
  - Adding new endpoints.
- **Breaking**
  - Removing or renaming endpoints.
  - Removing or renaming response fields.
  - Changing request/response field types incompatibly.
  - Tightening validation in a way that rejects previously valid requests.

## Versioning Rules

- Current stable namespace is `/api/v1`.
- Breaking changes require one of:
  - New versioned namespace (for example `/api/v2`), or
  - Compatibility shim in `/api/v1` with deprecation warning.

## Deprecation Rules

- Deprecated endpoints/fields must be announced in release notes.
- Deprecation must include:
  - exact affected path/field,
  - replacement path/field,
  - removal target release.

## CI Enforcement

- Backend OpenAPI schema is the source of truth.
- Contract parity checks run in CI and fail on drift for required dashboard routes.

## Migration Notes Template

For each breaking change, publish:

1. **What changed**
2. **Who is affected**
3. **How to migrate**
4. **Fallback/compatibility window**
5. **Removal timeline**
