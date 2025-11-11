export interface RecommendationsResponse {
  limit: number,
  model: string,
  recommendations: Array<Recommendations>,
  target_id: number,
  target_key: string,
  target_type: string
}

export interface Recommendations {
    generated_at: Date,
    items: Array<number>,
    model?: string
}