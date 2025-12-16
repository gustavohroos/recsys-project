import { useState, useEffect } from "react";
import { ThumbsUp, ThumbsDown } from "lucide-react";

const API_BASE_URL = "http://127.0.0.1:8000/api";

interface LikeDislikeProps {
  itemId: number; // ID do tópico/item para enviar ao backend
  userId?: number; // ID do usuário (opcional, default 1)
  onFeedbackChange?: (feedback: "like" | "dislike" | null) => void; // callback para notificar mudança
}

export default function LikeDislikeButton({ itemId, userId = 1, onFeedbackChange }: LikeDislikeProps) {
  const [status, setStatus] = useState<"like" | "dislike" | null>(null);
  const [loading, setLoading] = useState(false);

  // Buscar estado inicial do feedback ao montar o componente
  useEffect(() => {
    const fetchInitialFeedback = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/feedback/${userId}`);
        if (res.ok) {
          const data = await res.json();
          if (data.likes?.includes(itemId)) {
            setStatus("like");
          } else if (data.dislikes?.includes(itemId)) {
            setStatus("dislike");
          } else {
            setStatus(null);
          }
        }
      } catch (err) {
        console.error("Erro ao buscar feedback inicial:", err);
      }
    };

    fetchInitialFeedback();
  }, [itemId, userId]);

  const sendFeedback = async (newStatus: "like" | "dislike" | null) => {
    try {
      setLoading(true);

      await fetch(`${API_BASE_URL}/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          itemId,
          feedback: newStatus, // "like" | "dislike" | null
        }),
      });

      // Notificar componente pai sobre a mudança
      onFeedbackChange?.(newStatus);
    } catch (err) {
      console.error("Erro ao enviar feedback:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleLike = () => {
    const newStatus = status === "like" ? null : "like";
    setStatus(newStatus);
    sendFeedback(newStatus);
  };

  const handleDislike = () => {
    const newStatus = status === "dislike" ? null : "dislike";
    setStatus(newStatus);
    sendFeedback(newStatus);
  };

  return (
    <div className="flex items-center gap-4">
      <button
        disabled={loading}
        onClick={handleLike}
        className={`flex items-center gap-2 px-4 py-2 rounded-xl border transition shadow-sm cursor-pointer ${
          status === "like"
            ? "bg-blue-900 text-white border-blue-900"
            : "bg-white text-gray-800 border-gray-300 hover:bg-gray-100"
        }`}
      >
        <ThumbsUp size={20} />
      </button>

      <button
        disabled={loading}
        onClick={handleDislike}
        className={`flex items-center gap-2 px-4 py-2 rounded-xl border transition shadow-sm cursor-pointer ${
          status === "dislike"
            ? "bg-blue-900 text-white border-blue-900"
            : "bg-white text-gray-800 border-gray-300 hover:bg-gray-100"
        }`}
      >
        <ThumbsDown size={20} />
      </button>
    </div>
  );
}
