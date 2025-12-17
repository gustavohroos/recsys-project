import type {
  Category,
  PreferenceRecommendationsResponse,
  RecommendationsResponse,
} from "../types/Responses";
import type { Topic } from "../types/Topic";

const API_BASE_URL = "http://127.0.0.1:8000/api";

// Collaborative Filtering models
const users_model_name = "user_based_cf";
const itens_model_name = "item_based_cf";

// Users 1001 - 1070

export async function getAllItems(): Promise<Topic[]> {
  const res = await fetch(`${API_BASE_URL}/items`);

  if (!res.ok) {
    throw new Error("Failed to fetch items");
  }

  return res.json();
}

export async function getItemById(id: string | number): Promise<Topic> {
  const res = await fetch(`${API_BASE_URL}/items?ids=${id}`);

  if (!res.ok) {
    throw new Error(`Item with id ${id} not found`);
  }

  return res.json();
}

export async function getItemsByIds(ids: Array<number>): Promise<Topic[]> {
  const idsParam = ids.join(",");
  const res = await fetch(`${API_BASE_URL}/items?ids=${idsParam}`);

  if (!res.ok) {
    throw new Error(`Items with ids [${idsParam}] not found`);
  }

  return res.json();
}

export async function getRecommendationsByUser(
  userId: string | number,
  limit: number = 10
): Promise<RecommendationsResponse> {
  const res = await fetch(
    `${API_BASE_URL}/recommendations?user_id=${userId}&model=${users_model_name}&limit=${limit}`
  );

  if (!res.ok) {
    throw new Error(`Recommendations for user ${userId} not found`);
  }

  return res.json();
}

export async function getRecommendationsByItem(
  itemId: string | number,
  limit: number = 10
): Promise<RecommendationsResponse> {
  const res = await fetch(
    `${API_BASE_URL}/recommendations?item_id=${itemId}&model=${itens_model_name}&limit=${limit}`
  );

  if (!res.ok) {
    throw new Error(`Recommendations for item ${itemId} not found`);
  }

  return res.json();
}

// Categories API

export async function getAllCategories(): Promise<Category[]> {
  const res = await fetch(`${API_BASE_URL}/categories`);

  if (!res.ok) {
    throw new Error("Failed to fetch categories");
  }

  return res.json();
}

export async function getRecommendationsByPreferences(
  categories: string[],
  limit: number = 10
): Promise<PreferenceRecommendationsResponse> {
  const res = await fetch(`${API_BASE_URL}/recommendations/by-preferences`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ categories, limit }),
  });

  if (!res.ok) {
    throw new Error("Failed to get recommendations by preferences");
  }

  return res.json();
}

// Feedback-adjusted recommendations

export async function getRecommendationsWithFeedback(
  userId: string | number,
  model?: string,
  limit: number = 10
): Promise<RecommendationsResponse> {
  const params = new URLSearchParams({
    user_id: String(userId),
    limit: String(limit),
  });

  if (model) {
    params.set("model", model);
  }

  const res = await fetch(`${API_BASE_URL}/recommendations/with-feedback?${params.toString()}`);

  if (!res.ok) {
    throw new Error(`Feedback-adjusted recommendations for user ${userId} not found`);
  }

  return res.json();
}

// User feedback

export interface UserFeedback {
  user_id: number;
  likes: number[];
  dislikes: number[];
}

export async function getUserFeedback(userId: number): Promise<UserFeedback> {
  const res = await fetch(`${API_BASE_URL}/feedback/${userId}`);

  if (!res.ok) {
    throw new Error(`Failed to fetch feedback for user ${userId}`);
  }

  return res.json();
}

export interface ResetFeedbackResponse {
  status: string;
  message: string;
  deleted_count: number;
}

export async function resetAllFeedback(): Promise<ResetFeedbackResponse> {
  const res = await fetch(`${API_BASE_URL}/feedback/reset`, {
    method: "DELETE",
  });

  if (!res.ok) {
    throw new Error("Failed to reset feedback");
  }

  return res.json();
}

// Top Rated
export async function getTopRated(limit = 50, offset = 0) {
  const res = await fetch(`${API_BASE_URL}/top-rated?limit=${limit}&offset=${offset}`);
  if (!res.ok) throw new Error("Failed to fetch top-rated");
  return res.json();
}
