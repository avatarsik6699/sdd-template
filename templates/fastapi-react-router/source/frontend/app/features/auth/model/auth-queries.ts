import { useMutation, useQuery } from "@tanstack/react-query";

import { api } from "@shared/api/client";

export const authQueryKeys = {
  me: ["auth", "me"] as const,
};

export function useLoginMutation() {
  return useMutation({
    mutationFn: async (payload: { email: string; password: string }) => {
      const result = await api.post("/api/v1/auth/login", { body: payload });
      if (result.error) {
        throw result.error;
      }
      return result.data;
    },
  });
}

export function useMeQuery(token?: string) {
  return useQuery({
    queryKey: authQueryKeys.me,
    enabled: Boolean(token),
    queryFn: async () => {
      const result = await api.get("/api/v1/auth/me", {
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      });

      if (result.error) {
        throw result.error;
      }
      return result.data;
    },
  });
}
