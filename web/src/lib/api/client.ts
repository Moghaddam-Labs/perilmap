/**
 * Calls PerilMap's API. Locations and postcodes are only ever sent in the body of a request, never
 * in a web address, so they can't end up in browser history or anyone's logs.
 */

import { apiOrigin } from "@/lib/config";
import type { Position } from "@/lib/geo";
import type { Assessment, PostcodeResult } from "./types";

export type ApiProblem = "invalid" | "not_found" | "busy" | "unavailable";

export class ApiError extends Error {
  constructor(readonly problem: ApiProblem) {
    super(`PerilMap's API couldn't answer: ${problem}`);
    this.name = "ApiError";
  }
}

const TIMEOUT_MS = 10_000;

function problemFor(status: number): ApiProblem {
  if (status === 404) return "not_found";
  if (status === 422) return "invalid";
  if (status === 429) return "busy";
  return "unavailable";
}

async function postJson(path: string, body: unknown, signal?: AbortSignal): Promise<unknown> {
  const signals = [AbortSignal.timeout(TIMEOUT_MS), ...(signal ? [signal] : [])];
  let response: Response;
  try {
    response = await fetch(`${apiOrigin()}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      cache: "no-store",
      credentials: "omit",
      referrerPolicy: "no-referrer",
      signal: AbortSignal.any(signals),
    });
  } catch (error) {
    if (signal?.aborted) {
      throw error;
    }
    throw new ApiError("unavailable");
  }
  if (!response.ok) {
    throw new ApiError(problemFor(response.status));
  }
  try {
    return await response.json();
  } catch {
    throw new ApiError("unavailable");
  }
}

function isPostcodeResult(value: unknown): value is PostcodeResult {
  const result = value as Partial<PostcodeResult> | null;
  return (
    typeof result?.postcode === "string" &&
    Number.isFinite(result.latitude) &&
    Number.isFinite(result.longitude) &&
    typeof result.attribution === "string"
  );
}

export async function lookupPostcode(postcode: string, signal?: AbortSignal) {
  const result = await postJson("/v1/postcodes/lookup", { postcode }, signal);
  if (!isPostcodeResult(result)) {
    throw new ApiError("unavailable");
  }
  return result;
}

function isAssessment(value: unknown): value is Assessment {
  const result = value as Partial<Assessment> | null;
  return (
    typeof result?.available_here === "boolean" &&
    typeof result.disclaimer === "string" &&
    Array.isArray(result.results) &&
    Array.isArray(result.not_covered)
  );
}

/** Asks the API what's around a spot. About 10 cm is far more exact than any of the data. */
export async function assessLocation({ latitude, longitude }: Position, signal?: AbortSignal) {
  const round = (degrees: number) => Math.round(degrees * 1e6) / 1e6;
  const result = await postJson(
    "/v1/assessments",
    { latitude: round(latitude), longitude: round(longitude) },
    signal,
  );
  if (!isAssessment(result)) {
    throw new ApiError("unavailable");
  }
  return result;
}
