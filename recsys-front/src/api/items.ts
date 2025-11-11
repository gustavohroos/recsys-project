import type { Topic } from "../types/Topic";

const API_BASE_URL = "http://127.0.0.1:8000/api";

export async function getAllItems(): Promise<Topic[]> {
  const res = await fetch(`${API_BASE_URL}/items`);

  if (!res.ok) {
    throw new Error("Failed to fetch items");
  }

  return res.json();
}

export async function getItemById(id: string | number): Promise<Topic> {
  const res = await fetch(`${API_BASE_URL}/items/${id}`);

  if (!res.ok) {
    throw new Error(`Item with id ${id} not found`);
  }

  return res.json();
}