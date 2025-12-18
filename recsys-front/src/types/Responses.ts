export interface RecommendationsResponse {
  limit: number,
  model: string,
  recommendations: Array<Recommendations>,
  target_id: number,
  target_key: string,
  target_type: string
}

export interface itemRating {
  item_id: number;
  rating: number;
}

export interface UserFeedback {
  user_id: number;
  items: itemRating[];
}

export interface User {
  id: number;
  name: string;
  email: string;
  picture?: string;
}

export interface Recommendations {
  generated_at: Date,
  items: Array<RecommendedItem>,
  model?: string
}

export interface RecommendedItem {
  item_id: number,
  score: number | null
}

export interface Category {
  id: string;
  name: string;
  description: string;
  icon: string;
  item_count: number;
}

export interface PreferenceRecommendationsResponse {
  categories: string[];
  limit: number;
  items: Array<RecommendedItem>;
}