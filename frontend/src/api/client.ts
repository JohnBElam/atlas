import axios from "axios";

export interface ApiEnvelope<T> {
  data: T | null;
  error: string | null;
  meta: Record<string, unknown>;
}

export interface PaginationMeta {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

const API_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000/api/v1";

export function getWebSocketUrl(path: string): string {
  const base = API_URL.replace(/^http/, "ws");
  return `${base}${path.startsWith("/") ? path : `/${path}`}`;
}

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
});

function rethrowEnvelopeError(err: unknown): never {
  if (axios.isAxiosError(err)) {
    const envelopeError = err.response?.data?.error;
    if (typeof envelopeError === "string" && envelopeError.length > 0) {
      throw new Error(envelopeError);
    }
  }
  throw err;
}

async function readEnvelope<T>(
  request: () => Promise<{ data: ApiEnvelope<T> }>,
): Promise<ApiEnvelope<T>> {
  try {
    const response = await request();
    if (response.data.error) {
      throw new Error(response.data.error);
    }
    return response.data;
  } catch (err) {
    rethrowEnvelopeError(err);
  }
}

export async function getEnvelope<T>(url: string, params?: Record<string, unknown>): Promise<ApiEnvelope<T>> {
  return readEnvelope(() => apiClient.get<ApiEnvelope<T>>(url, { params }));
}

export async function postEnvelope<T>(url: string, body?: unknown): Promise<ApiEnvelope<T>> {
  return readEnvelope(() => apiClient.post<ApiEnvelope<T>>(url, body));
}

export async function putEnvelope<T>(url: string, body?: unknown): Promise<ApiEnvelope<T>> {
  return readEnvelope(() => apiClient.put<ApiEnvelope<T>>(url, body));
}

export async function deleteEnvelope<T>(url: string): Promise<ApiEnvelope<T>> {
  return readEnvelope(() => apiClient.delete<ApiEnvelope<T>>(url));
}
