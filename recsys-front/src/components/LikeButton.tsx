import { useState } from "react";
import { ThumbsUp, ThumbsDown } from "lucide-react";

interface LikeDislikeProps {
  itemId: number; // ID do tópico/item para enviar ao backend
}

export default function LikeDislikeButton({ itemId }: LikeDislikeProps) {
  const [status, setStatus] = useState<"like" | "dislike" | null>(null);
  const [loading, setLoading] = useState(false);

  const sendFeedback = async (newStatus: "like" | "dislike" | null) => {
    try {
      setLoading(true);

      await fetch("/api/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          itemId,
          feedback: newStatus, // "like" | "dislike" | null
        }),
      });
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
        className={`flex items-center gap-2 px-4 py-2 rounded-xl border transition shadow-sm ${
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
        className={`flex items-center gap-2 px-4 py-2 rounded-xl border transition shadow-sm ${
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
