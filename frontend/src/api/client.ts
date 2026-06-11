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

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
});

export async function getEnvelope<T>(url: string, params?: Record<string, unknown>): Promise<ApiEnvelope<T>> {
  const response = await apiClient.get<ApiEnvelope<T>>(url, { params });
  if (response.data.error) {
    throw new Error(response.data.error);
  }
  return response.data;
}

export async function postEnvelope<T>(url: string, body?: unknown): Promise<ApiEnvelope<T>> {
  const response = await apiClient.post<ApiEnvelope<T>>(url, body);
  if (response.data.error) {
    throw new Error(response.data.error);
  }
  return response.data;
}

export async function putEnvelope<T>(url: string, body?: unknown): Promise<ApiEnvelope<T>> {
  const response = await apiClient.put<ApiEnvelope<T>>(url, body);
  if (response.data.error) {
    throw new Error(response.data.error);
  }
  return response.data;
}

export async function deleteEnvelope<T>(url: string): Promise<ApiEnvelope<T>> {
  const response = await apiClient.delete<ApiEnvelope<T>>(url);
  if (response.data.error) {
    throw new Error(response.data.error);
  }
  return response.data;
}
