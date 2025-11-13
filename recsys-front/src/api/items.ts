import type { RecommendationsResponse } from "../types/Responses";
import type { Topic } from "../types/Topic";

const API_BASE_URL = "http://127.0.0.1:8000/api";

const users_model_name = "random";
const itens_model_name = "item_similarity";

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
