import type { paths } from "@shared/types/schema";

// --- Type utilities (framework-agnostic, derived from openapi-typescript output) ---

type HttpMethod = "get" | "post" | "put" | "delete" | "patch";

export type ExtractResponse<
  Path extends keyof paths,
  Method extends HttpMethod,
> = paths[Path] extends Record<Method, unknown>
  ? paths[Path][Method] extends {
      responses: { 200: { content: { "application/json": infer Res } } };
    }
    ? Res
    : paths[Path][Method] extends {
          responses: { 201: { content: { "application/json": infer Res201 } } };
        }
      ? Res201
      : unknown
  : unknown;

export type ExtractBody<
  Path extends keyof paths,
  Method extends HttpMethod,
> = paths[Path] extends Record<Method, unknown>
  ? paths[Path][Method] extends {
      requestBody: { content: { "application/json": infer Body } };
    }
    ? Body
    : paths[Path][Method] extends {
          requestBody?: { content: { "application/json": infer OptionalBody } };
        }
      ? OptionalBody | undefined
      : undefined
  : undefined;

export type ExtractQuery<
  Path extends keyof paths,
  Method extends HttpMethod,
> = paths[Path] extends Record<Method, unknown>
  ? paths[Path][Method] extends { parameters: { query?: infer Query } }
    ? Query
    : undefined
  : undefined;

export type ExtractPathParams<
  Path extends keyof paths,
  Method extends HttpMethod,
> = paths[Path] extends Record<Method, unknown>
  ? paths[Path][Method] extends { parameters: { path?: infer P } }
    ? P
    : undefined
  : undefined;

// --- Result type ---

export type ApiResult<T> =
  | { data: T; error: null; status: number }
  | { data: null; error: { status: number; detail: unknown }; status: number };

// --- Internal helpers ---

interface RequestOptions<Path extends keyof paths, Method extends HttpMethod> {
  body?: ExtractBody<Path, Method>;
  query?: ExtractQuery<Path, Method>;
  params?: ExtractPathParams<Path, Method>;
  headers?: HeadersInit;
  signal?: AbortSignal;
}

function interpolatePath(
  path: string,
  params?: Record<string, string | number>,
): string {
  if (!params) return path;
  return path.replace(
    /\{([^}]+)\}/g,
    (_, key) => String((params as Record<string, unknown>)[key] ?? key),
  );
}

function buildUrl(
  baseUrl: string,
  path: string,
  query?: Record<string, unknown>,
): string {
  const base = baseUrl.endsWith("/") ? baseUrl : `${baseUrl}/`;
  const url = new URL(path.startsWith("/") ? path.slice(1) : path, base);
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined && value !== null) {
        url.searchParams.set(key, String(value));
      }
    }
  }
  return url.toString();
}

async function request<Path extends keyof paths, Method extends HttpMethod>(
  baseUrl: string,
  method: Method,
  path: Path,
  options: RequestOptions<Path, Method> = {},
): Promise<ApiResult<ExtractResponse<Path, Method>>> {
  const resolvedPath = interpolatePath(
    path as string,
    options.params as Record<string, string | number> | undefined,
  );
  const url = buildUrl(
    baseUrl,
    resolvedPath,
    options.query as Record<string, unknown> | undefined,
  );

  const headers = new Headers(options.headers);
  if (options.body !== undefined && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  let response: Response;
  try {
    response = await fetch(url, {
      method: method.toUpperCase(),
      headers,
      body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
      signal: options.signal,
    });
  } catch (err) {
    return { data: null, error: { status: 0, detail: err }, status: 0 };
  }

  if (!response.ok) {
    let detail: unknown;
    try {
      detail = await response.json();
    } catch {
      detail = await response.text();
    }
    return {
      data: null,
      error: { status: response.status, detail },
      status: response.status,
    };
  }

  const data = (await response.json()) as ExtractResponse<Path, Method>;
  return { data, error: null, status: response.status };
}

// --- API client factory ---

function createApiClient(baseUrl: string) {
  return {
    get: <Path extends keyof paths>(
      path: Path,
      options?: RequestOptions<Path, "get">,
    ) => request(baseUrl, "get", path, options),

    post: <Path extends keyof paths>(
      path: Path,
      options?: RequestOptions<Path, "post">,
    ) => request(baseUrl, "post", path, options),

    put: <Path extends keyof paths>(
      path: Path,
      options?: RequestOptions<Path, "put">,
    ) => request(baseUrl, "put", path, options),

    patch: <Path extends keyof paths>(
      path: Path,
      options?: RequestOptions<Path, "patch">,
    ) => request(baseUrl, "patch", path, options),

    delete: <Path extends keyof paths>(
      path: Path,
      options?: RequestOptions<Path, "delete">,
    ) => request(baseUrl, "delete", path, options),
  };
}

export const api = createApiClient(
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000",
);
