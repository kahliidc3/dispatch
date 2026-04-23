import { ApiError } from "@/lib/api/errors";

export async function serverJson<T>(input: string, init?: RequestInit) {
  const response = await fetch(input, {
    ...init,
    headers: {
      Accept: "application/json",
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    throw new ApiError(`Request failed for ${input}`, response.status);
  }

  return (await response.json()) as T;
}
