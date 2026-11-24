import createClient from "openapi-fetch";
import type { components, paths } from "./schema";

export type { components, paths };
export type Schemas = components["schemas"];
export type Verification = Schemas["VerificationEnum"];

/** Typed client generated from the OpenAPI schema (the contract). */
export function createApi(baseUrl: string, fetchImpl?: typeof fetch) {
  return createClient<paths>({ baseUrl, fetch: fetchImpl });
}
export type Api = ReturnType<typeof createApi>;
