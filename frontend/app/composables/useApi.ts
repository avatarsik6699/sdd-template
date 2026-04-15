/**
 * useApi — thin wrapper over $fetch that automatically attaches the JWT
 * Authorization header from the auth store and redirects to /login on 401.
 */
export function useApi() {
  const config = useRuntimeConfig()
  const authStore = useAuthStore()
  const baseURL = config.public.apiBase as string

  async function apiFetch<T>(
    path: string,
    options: Parameters<typeof $fetch>[1] = {}
  ): Promise<T> {
    const headers: Record<string, string> = {
      ...(options.headers as Record<string, string> | undefined ?? {}),
      ...authStore.authHeader,
    }

    try {
      return await $fetch<T>(`${baseURL}${path}`, { ...options, headers })
    } catch (err: unknown) {
      const status = (err as { status?: number })?.status
      if (status === 401) {
        authStore.logout()
      }
      throw err
    }
  }

  return { apiFetch }
}
