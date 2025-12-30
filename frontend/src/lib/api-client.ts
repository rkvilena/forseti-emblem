/**
 * API Client for Forsetiemblem Backend
 *
 * Centralized API communication layer with error handling.
 */

import type {
  ChatResponse,
  RagChatRequest,
  HealthResponse,
  ApiError,
} from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Custom error class for API errors
 */
export class ApiClientError extends Error {
  constructor(
    message: string,
    public status: number,
    public detail?: string,
  ) {
    super(message);
    this.name = "ApiClientError";
  }
}

/**
 * Generic fetch wrapper with error handling
 */
async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const defaultHeaders: HeadersInit = {
    "Content-Type": "application/json",
  };

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    });

    if (!response.ok) {
      let errorDetail: string | undefined;

      try {
        const errorData = (await response.json()) as ApiError;
        errorDetail = errorData.detail;
      } catch {
        errorDetail = response.statusText;
      }

      throw new ApiClientError(
        `API request failed: ${response.status}`,
        response.status,
        errorDetail,
      );
    }

    return response.json() as Promise<T>;
  } catch (error) {
    if (error instanceof ApiClientError) {
      throw error;
    }

    // Network or other errors
    throw new ApiClientError(
      "Failed to connect to the API server",
      0,
      error instanceof Error ? error.message : "Unknown error",
    );
  }
}

/**
 * API Client object with all available endpoints
 */
export const apiClient = {
  /**
   * Health check endpoint
   */
  health: async (): Promise<HealthResponse> => {
    return apiFetch<HealthResponse>("/health");
  },

  /**
   * RAG-powered chat endpoint
   * This is the main endpoint for Fire Emblem chapter questions
   */
  chatRag: async (request: RagChatRequest): Promise<ChatResponse> => {
    return apiFetch<ChatResponse>("/chat/rag", {
      method: "POST",
      body: JSON.stringify(request),
    });
  },
};

export default apiClient;
