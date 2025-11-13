import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useState } from "react";
import {
  getItemsByIds,
  getRecommendationsByItem,
  getRecommendationsByUser,
} from "../api/items";
import UserCard from "../components/UserCard";
import type { Topic } from "../types/Topic";
import LikeDislikeButton from "../components/LikeButton";

const randomUserId = Math.floor(Math.random() * 70) + 1001;

export default function Home() {
  const [selectedTopic, setSelectedTopic] = useState<Topic | null>(null);
  const [userRecommendations, setUserRecommendations] = useState<Topic[]>([]);
  const [itemRecommendations, setItemRecommendations] = useState<Topic[]>([]);
  const [userId, setUserId] = useState(1001);

  useEffect(() => {
    (async () => {
      try {
        const recResponse = await getRecommendationsByUser(randomUserId);
        const itemIds = recResponse.recommendations[0].items;
        let items = await getItemsByIds(itemIds);
        items = (Array.isArray(items) ? items : []).map((item: any) => ({
          ...item,
          image: `https://picsum.photos/200?random=${Math.random()}`,
        }));

        if (items.length > 0) {
          setUserRecommendations(items as Topic[]);
          setSelectedTopic((prev) => prev ?? (items[0] as Topic));
        }
      } catch (err) {
        console.error("Failed to fetch items:", err);
      }
    })();
  }, [userId]);

  useEffect(() => {
    if (!selectedTopic) return;

    (async () => {
      try {
        const recResponse = await getRecommendationsByItem(selectedTopic.id);
        const itemIds = recResponse.recommendations[0].items;
        let items = await getItemsByIds(itemIds);

        items = (Array.isArray(items) ? items : []).map((item: any) => ({
          ...item,
          image: `https://picsum.photos/200?random=${Math.random()}`,
        }));

        if (items.length > 0) {
          setItemRecommendations(items as Topic[]);
        }
      } catch (err) {
        console.error("Failed to fetch items:", err);
      }
    })();
  }, [selectedTopic]);

  return (
    <div className="w-full min-h-screen bg-gray-800 flex">
      {/* COLUNA 1 — USUÁRIO */}
      <div className="w-72 min-h-screen p-6 bg-gray-900 flex items-start justify-center">
        <UserCard
          name="User"
          email="ulian@empresa.com"
          role="X"
          avatarUrl="https://i.pravatar.cc/150?img=65"
          currentUserId={userId}
          onUserChange={setUserId}
        />
      </div>

      {/* COLUNA 2 — LISTA + DETALHES */}
      <div className="flex-1 min-h-screen p-6 flex justify-center bg-gray-100">
        <div className="w-full max-w-5xl bg-white rounded-xl shadow-xl p-6">
          <div className="flex w-full rounded-xl overflow-hidden border border-gray-200">
            {/* LISTA DE TÓPICOS */}
            <div className="w-1/3 border-r border-gray-200 p-6 bg-gray-50">
              <h1 className="text-xl font-semibold mb-4 text-gray-900">
                Tópicos
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
                          src={topic.image}
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
                      src={selectedTopic.image}
                      alt={selectedTopic.title}
                      className="w-64 h-64 rounded-xl object-cover shadow mb-6"
                    />

                    <p className="text-gray-700 leading-relaxed">
                      {selectedTopic.description}
                    </p>

                    <LikeDislikeButton itemId={Number(selectedTopic.id)} />

                    <div className="mt-4 text-sm text-gray-600">
                      Score: <strong>{selectedTopic.score}</strong>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </div>
      </div>

      {/* RELACIONADOS */}
      <div className="w-80 min-h-screen p-6 bg-gray-900 text-white">
        <h1 className="text-xl font-semibold mb-4">Relacionados</h1>
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
                      setSelectedTopic({
                        ...selectedTopic,
                        title: related.title,
                      })
                    }
                    className="w-full text-left p-4 rounded-lg bg-gray-800 border border-gray-700 transition"
                  >
                    <div className="flex items-center gap-3">
                      <img
                        src={related.image}
                        alt={related.title}
                        className="w-10 h-10 rounded-lg object-cover"
                      />
                      <span className="text-sm">{related.title}</span>
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
