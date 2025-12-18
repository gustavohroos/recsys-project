import { useEffect, useState } from "react";
import type { Topic } from "../types/Topic";
import { getUserFeedback, getItemsByIds } from "../api/items";

interface UserLikedItemsProps {
  userId: number;
  refreshKey: number;
  setSelectedTopic: (topic: Topic) => void;
}

export default function UserLikedItems({ userId, refreshKey, setSelectedTopic }: UserLikedItemsProps) {
  const [likedItems, setLikedItems] = useState<Topic[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadLikedItems() {
      try {
        const feedback = await getUserFeedback(userId);

        // 👇 aqui está o ponto-chave
        const ratedItems = feedback.items;

        const likedIds = ratedItems
          .map((item) => item.item_id);

        if (likedIds.length === 0) {
          setLikedItems([]);
          setLoading(false);
          return;
        }

        const items = await getItemsByIds(likedIds);
        setLikedItems(items);
      } catch (error) {
        console.error(error);
        setLikedItems([]);
      } finally {
        setLoading(false);
      }
    }

    loadLikedItems();
  }, [userId, refreshKey]);

  return (
    <div className="mt-4 w-full flex flex-col gap-3 p-6 bg-white border border-gray-200 rounded-xl shadow-sm">
      <h2 className="text-sm font-semibold text-gray-800">Itens Avaliados</h2>

      {loading ? (
        <p className="text-sm text-gray-500">Carregando itens avaliados...</p>
      ) : likedItems.length === 0 ? (
        <p className="text-sm text-gray-500">
          Este usuário ainda não avaliou nenhum item.
        </p>
      ) : (
        <ul className="flex flex-col gap-2">
          {likedItems.map((item) => (
            <li
              key={item.id}
              className="
                p-3 rounded-lg border border-gray-200 bg-gray-50
                text-sm text-gray-800
                hover:bg-blue-50 hover:border-blue-300
                transition cursor-pointer
              "
              onClick={() => setSelectedTopic(item)}
            >
              <span className="font-medium">{item.title}</span>
              <span className="ml-2 text-xs text-gray-500">
                (ID {item.id})
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
