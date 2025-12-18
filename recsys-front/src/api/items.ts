import type { Category, PreferenceRecommendationsResponse, RecommendationsResponse } from "../types/Responses";
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

  const res = await fetch(
    `${API_BASE_URL}/recommendations/with-feedback?${params.toString()}`
  );

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

// Demo API

export interface DemoCFResponse {
  scenario: {
    user_1_id: number;
    user_2_id: number;
    user_1_likes: number[];
    user_2_likes: number[];
    expected_recommendation_for_user_1: number;
  };
  recommendations_for_user_1: Array<{ item_id: number; score: number }>;
}

export async function runCollaborativeFilteringDemo(params: {
  user_1_id: number;
  user_2_id: number;
  item_x_id: number;
  item_y_id: number;
  item_z_id: number;
}): Promise<DemoCFResponse> {
  const res = await fetch(`${API_BASE_URL}/demo/cf`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });

  if (!res.ok) {
    throw new Error("Failed to run collaborative filtering demo");
  }

  return res.json();
}

export interface DemoCFRealResponse {
  user_1_id: number;
  user_2_id: number;
  item_x_id: number;
  item_y_id: number;
  item_z_id: number;
  item_w_id: number;
  z_rank: number | null;
  recommendations: Array<{ item_id: number; score?: number }>;
  items: {
    x: Topic;
    y: Topic;
    z: Topic;
    w: Topic;
  };
}

export async function runCollaborativeFilteringRealDemo(): Promise<DemoCFRealResponse> {
  const res = await fetch(`${API_BASE_URL}/demo/cf-real`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "Failed to run real CF demo");
  }

  return res.json();
}
