# ADR 0006: OpenAPI schema is the contract
Status: accepted
Decision: drf-spectacular produces `packages/api-client/openapi.json`; the TS types are generated with openapi-typescript and consumed through openapi-fetch. CI regenerates and fails on `git diff`.
