import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useMemo, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import {
  getItemsByIds,
  getRecommendationsByItem,
  getRecommendationsWithFeedback,
  resetAllFeedback,
} from "../api/items";
import UserCard from "../components/UserCard";
import type { Topic } from "../types/Topic";
import LikeDislikeButton from "../components/LikeButton";

export default function Home() {
  const [selectedTopic, setSelectedTopic] = useState<Topic | null>(null);
  const [userRecommendations, setUserRecommendations] = useState<Topic[]>([]);
  const [itemRecommendations, setItemRecommendations] = useState<Topic[]>([]);
  const [userId, setUserId] = useState(1001);
  const [refreshKey, setRefreshKey] = useState(0); // Para forçar refresh após feedback

  const mergeItemsWithScores = useMemo(
    () =>
      (items: Topic[], scoredItems: Array<{ item_id: number; score: number | null }>) => {
        const scoreMap = new Map<number, number | null>();
        scoredItems.forEach((entry) => {
          scoreMap.set(entry.item_id, entry.score ?? null);
        });

        return items
          .map((item) => {
            const numericId = Number(item.id);
            const score = scoreMap.get(numericId) ?? null;
            return {
              ...item,
              score: score ?? undefined,
            };
          })
          .sort((a, b) => (b.score ?? 0) - (a.score ?? 0));
      },
    []
  );

  // Função para recarregar recomendações após mudança de feedback
  const handleFeedbackChange = useCallback((feedback: "like" | "dislike" | null) => {
    // Se foi um dislike, recarregar as recomendações
    if (feedback === "dislike") {
      setRefreshKey((prev) => prev + 1);
    }
  }, []);

  // Número de itens a exibir na lista
  const DISPLAY_LIMIT = 10;

  useEffect(() => {
    (async () => {
      try {
        // Buscar mais itens do que o necessário para compensar os filtrados por feedback
        // O backend já filtra os dislikes, então pedimos um limite maior
        const recResponse = await getRecommendationsWithFeedback(userId, "user_based_cf", 30);
        const scoredItems = recResponse.recommendations[0]?.items ?? [];
        // Limitar para exibição
        const limitedItems = scoredItems.slice(0, DISPLAY_LIMIT);
        const itemIds = limitedItems.map((item: { item_id: number }) => item.item_id);

        if (itemIds.length === 0) {
          setUserRecommendations([]);
          setSelectedTopic(null);
          return;
        }

        const items = await getItemsByIds(itemIds);
        const merged = mergeItemsWithScores(items as Topic[], limitedItems);

        if (merged.length > 0) {
          setUserRecommendations(merged);
          setSelectedTopic((prev) => {
            if (prev) {
              const updated = merged.find((topic) => String(topic.id) === String(prev.id));
              return updated ?? merged[0];
            }
            return merged[0];
          });
        }
      } catch (err) {
        console.error("Failed to fetch items:", err);
      }
    })();
  }, [userId, refreshKey, mergeItemsWithScores]);

  useEffect(() => {
    if (!selectedTopic) return;

    (async () => {
      try {
        const recResponse = await getRecommendationsByItem(selectedTopic.id);
        const scoredItems = recResponse.recommendations[0]?.items ?? [];
        const itemIds = scoredItems.map((item) => item.item_id);

        if (itemIds.length === 0) {
          setItemRecommendations([]);
          return;
        }

        const items = await getItemsByIds(itemIds);
        const merged = mergeItemsWithScores(items as Topic[], scoredItems);
        setItemRecommendations(merged);
      } catch (err) {
        console.error("Failed to fetch items:", err);
      }
    })();
  }, [selectedTopic, mergeItemsWithScores]);

  return (
    <div className="w-full min-h-screen bg-gray-800 flex">
      {/* COLUNA 1 — USUÁRIO */}
      <div className="w-72 min-h-screen p-6 bg-gray-900 flex flex-col items-center">
        <UserCard
          name="User"
          email="ulian@empresa.com"
          role="X"
          avatarUrl="https://i.pravatar.cc/150?img=65"
          currentUserId={userId}
          onUserChange={setUserId}
        />

        {/* Link para Onboarding */}
        <Link
          to="/onboarding"
          className="mt-6 w-full px-4 py-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-lg text-center font-medium hover:from-blue-600 hover:to-purple-600 transition-all shadow-lg hover:shadow-xl"
        >
          🎯 Selecionar Preferências
        </Link>

        {/* Botão para resetar feedback */}
        <button
          onClick={async () => {
            if (window.confirm("Tem certeza que deseja resetar todos os likes e dislikes de todos os usuários?")) {
              try {
                const result = await resetAllFeedback();
                alert(`${result.message} (${result.deleted_count} registros removidos)`);
                setRefreshKey((prev) => prev + 1);
              } catch (err) {
                console.error("Erro ao resetar feedback:", err);
                alert("Erro ao resetar feedback");
              }
            }
          }}
          className="mt-3 w-full px-4 py-3 bg-red-600 text-white rounded-lg text-center font-medium hover:bg-red-700 transition-all shadow-lg hover:shadow-xl"
        >
          🗑️ Resetar Feedbacks
        </button>
      </div>

      {/* COLUNA 2 — LISTA + DETALHES */}
      <div className="flex-1 min-h-screen p-6 flex justify-center bg-gray-100">
        <div className="w-full max-w-5xl bg-white rounded-xl shadow-xl p-6">
          <div className="flex w-full rounded-xl overflow-hidden border border-gray-200">
            {/* LISTA DE TÓPICOS */}
            <div className="w-1/3 border-r border-gray-200 p-6 bg-gray-50">
              <h1 className="text-xl font-semibold mb-4 text-gray-900">
                Recomendações Personalizadas ao Usuário
              </h1>
              <ul className="flex flex-col gap-3">
                {userRecommendations.map((topic) => (
                  <li key={topic.id}>
                    <motion.button
                      whileHover={{
                        scale: 1.02,
                        boxShadow: "0px 4px 12px rgba(0,0,0,0.15)",
                      }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => setSelectedTopic(topic)}
                      className={`w-full text-left p-4 rounded-lg border transition ${
                        selectedTopic?.id === topic.id
                          ? "bg-blue-100 border-blue-300"
                          : "bg-white border-gray-200"
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <img
                          src={topic.image_url}
                          alt={topic.title}
                          className="w-12 h-12 rounded-lg object-cover"
                        />
                        <div>
                          <h2 className="text-sm font-medium text-gray-900">
                            {topic.title}
                          </h2>
                          <p className="text-xs text-gray-600 line-clamp-2">
                            {topic.description}
                          </p>
                          {topic.score !== undefined ? (
                            <p className="mt-1 text-xs text-gray-500">
                              Score: {topic.score.toFixed(3)}
                            </p>
                          ) : null}
                        </div>
                      </div>
                    </motion.button>
                  </li>
                ))}
              </ul>
            </div>

            {/* DETALHES DO TÓPICO */}
            <div className="w-2/3 p-8 bg-white">
              <AnimatePresence mode="wait">
                {!selectedTopic ? (
                  <motion.p
                    key="empty"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="text-gray-500 text-center mt-20"
                  >
                    Selecione um tópico na lista à esquerda.
                  </motion.p>
                ) : (
                  <motion.div
                    key={selectedTopic.id}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    transition={{ duration: 0.25 }}
                  >
                    <h2 className="text-2xl font-bold text-gray-900 mb-4">
                      {selectedTopic.title}
                    </h2>

                    <motion.img
                      layoutId={`img-${selectedTopic.id}`}
                      src={selectedTopic.image_url}
                      alt={selectedTopic.title}
                      className="w-64 h-64 rounded-xl object-cover shadow mb-6"
                    />

                    <p className="text-gray-700 leading-relaxed">
                      {selectedTopic.description}
                    </p>

                    <div className="mt-2">
                      <LikeDislikeButton
                        itemId={Number(selectedTopic.id)}
                        userId={userId}
                        onFeedbackChange={handleFeedbackChange}
                      />
                    </div>


                    {selectedTopic.score !== undefined ? (
                      <div className="mt-6 text-sm text-gray-600">
                        Score: <strong>{selectedTopic.score.toFixed(3)}</strong>
                      </div>
                    ) : null}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </div>
      </div>

      {/* RELACIONADOS */}
      <div className="w-80 min-h-screen p-6 bg-gray-900 text-white">
        <h1 className="text-xl font-semibold mb-4">Relacionados ao Item em Foco</h1>
        <AnimatePresence>
          {selectedTopic ? (
            <motion.ul
              key={selectedTopic.id}
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.25 }}
              className="flex flex-col gap-3"
            >
              {itemRecommendations.map((related) => (
                <li key={related.id}>
                  <motion.button
                    whileHover={{ scale: 1.02, backgroundColor: "#3a3a3a" }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() =>
                      setSelectedTopic(related)
                    }
                    className="w-full text-left p-4 rounded-lg bg-gray-800 border border-gray-700 transition"
                  >
                    <div className="flex items-center gap-3">
                      <img
                        src={related.image_url}
                        alt={related.title}
                        className="w-10 h-10 rounded-lg object-cover"
                      />
                      <span className="text-sm">
                        {related.title}
                        {related.score !== undefined
                          ? ` • ${related.score.toFixed(3)}`
                          : ""}
                      </span>
                    </div>
                  </motion.button>
                </li>
              ))}
            </motion.ul>
          ) : null}
        </AnimatePresence>
      </div>
    </div>
  );
}
