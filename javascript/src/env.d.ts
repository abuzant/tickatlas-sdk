/**
 * Minimal ambient declarations so the SDK compiles for BOTH Node and the
 * browser without forcing consumers to install `@types/node`.
 *
 * We only declare the *narrow* slice of `process` the SDK touches (reading two
 * env vars and feature-detecting Node via `process.versions.node`). Everything
 * else the SDK uses — `fetch`, `AbortController`, `setTimeout`, `URLSearchParams`,
 * `Headers` — already exists in the TS DOM lib and the ES2021 target.
 *
 * `process` is declared as possibly-`undefined` so the browser guard
 * (`typeof process !== "undefined"`) is type-safe.
 */

declare const process:
  | {
      env?: Record<string, string | undefined>;
      versions?: { node?: string };
    }
  | undefined;
