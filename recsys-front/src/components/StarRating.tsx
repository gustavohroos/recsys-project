import { useEffect, useState } from "react";
import { Star } from "lucide-react";

const API_BASE_URL = "http://127.0.0.1:8000/api";

interface StarRatingProps {
  itemId: number;
  userId?: number;
  onFeedbackChange?: (rating: number | null) => void;
}

export default function StarRating({
  itemId,
  userId = 1,
  onFeedbackChange,
}: StarRatingProps) {
  const [rating, setRating] = useState<number | null>(null);
  const [hover, setHover] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);

  // Buscar rating inicial
  useEffect(() => {
    async function fetchInitialRating() {
      try {
        const res = await fetch(`${API_BASE_URL}/feedback/${userId}`);
        if (!res.ok) return;

        const data = await res.json();

        // supondo formato: { ratings: { [itemId]: number } }
        const initialRating = data.ratings?.[itemId] ?? null;
        setRating(initialRating);
      } catch (err) {
        console.error("Erro ao buscar rating:", err);
      }
    }

    fetchInitialRating();
  }, [itemId, userId]);

  const sendRating = async (value: number | null) => {
    try {
      setLoading(true);

      await fetch(`${API_BASE_URL}/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          item_id: itemId,
          rating: value,
        }),
      });

      onFeedbackChange?.(value);
    } catch (err) {
      console.error("Erro ao enviar rating:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleClick = (value: number) => {
    const newRating = rating === value ? null : value;
    setRating(newRating);
    sendRating(newRating);
  };

  return (
    <div className="flex items-center gap-1 mt-4">
      {[1, 2, 3, 4, 5].map((star) => {
        const active = (hover ?? rating ?? 0) >= star;

        return (
          <button
            key={star}
            disabled={loading}
            onClick={() => handleClick(star)}
            onMouseEnter={() => setHover(star)}
            onMouseLeave={() => setHover(null)}
            className="transition transform hover:scale-110"
          >
            <Star
              size={28}
              className={`${
                active ? "fill-yellow-400 text-yellow-400" : "text-gray-400"
              }`}
            />
          </button>
        );
      })}
    </div>
  );
}
