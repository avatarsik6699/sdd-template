import type { UseFetchOptions } from 'nuxt/app';
import type { paths } from '@shared/types/schema';
import { useNuxtApp, useFetch } from '#imports';

type HttpMethod = 'get' | 'post' | 'put' | 'delete' | 'patch';

// Helper to extract response type from openapi-typescript schema
export type ExtractResponse<Path extends keyof paths, Method extends HttpMethod> =
  paths[Path] extends Record<Method, any>
    ? paths[Path][Method] extends {
        responses: { 200: { content: { 'application/json': infer Res } } };
      }
      ? Res
      : // Also check 201 for POST creations
        paths[Path][Method] extends {
            responses: { 201: { content: { 'application/json': infer Res201 } } };
          }
        ? Res201
        : unknown
    : unknown;

// Helper to extract body type from openapi-typescript schema
export type ExtractBody<Path extends keyof paths, Method extends HttpMethod> =
  paths[Path] extends Record<Method, any>
    ? paths[Path][Method] extends { requestBody: { content: { 'application/json': infer Body } } }
      ? Body
      : paths[Path][Method] extends {
            requestBody?: { content: { 'application/json': infer OptionalBody } };
          }
        ? OptionalBody | undefined
        : undefined
    : undefined;

// Helper to extract query type from openapi-typescript schema
export type ExtractQuery<Path extends keyof paths, Method extends HttpMethod> =
  paths[Path] extends Record<Method, any>
    ? paths[Path][Method] extends { parameters: { query?: infer Query } }
      ? Query
      : undefined
    : undefined;

export function useApiFetch<
  Path extends keyof paths,
  Method extends HttpMethod = Extract<keyof paths[Path], HttpMethod> extends never
    ? never
    : Extract<keyof paths[Path], HttpMethod>,
>(
  url: Path,
  options?: UseFetchOptions<ExtractResponse<Path, Method>> & {
    method?: Method;
    body?: ExtractBody<Path, Method>;
    query?: ExtractQuery<Path, Method>;
  }
) {
  const { $api } = useNuxtApp();

  return useFetch(url as string, {
    ...options,
    $fetch: $api,
  });
}
