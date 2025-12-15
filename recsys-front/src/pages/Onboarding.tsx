import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getAllCategories, getItemsByIds, getRecommendationsByPreferences } from "../api/items";
import type { Category } from "../types/Responses";
import type { Topic } from "../types/Topic";

export default function Onboarding() {
  const navigate = useNavigate();
  const [categories, setCategories] = useState<Category[]>([]);
  const [selectedCategories, setSelectedCategories] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [showRecommendations, setShowRecommendations] = useState(false);
  const [recommendations, setRecommendations] = useState<Topic[]>([]);
  const [loadingRecs, setLoadingRecs] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const cats = await getAllCategories();
        setCategories(cats);
      } catch (err) {
        console.error("Failed to fetch categories:", err);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const toggleCategory = (categoryId: string) => {
    setSelectedCategories((prev) => {
      const next = new Set(prev);
      if (next.has(categoryId)) {
        next.delete(categoryId);
      } else {
        next.add(categoryId);
      }
      return next;
    });
  };

  const handleGetRecommendations = async () => {
    if (selectedCategories.size === 0) return;

    setLoadingRecs(true);
    try {
      const response = await getRecommendationsByPreferences(
        Array.from(selectedCategories),
        12
      );

      const itemIds = response.items.map((item) => item.item_id);
      if (itemIds.length > 0) {
        const items = await getItemsByIds(itemIds);

        // Merge scores with items
        const scoreMap = new Map(
          response.items.map((item) => [item.item_id, item.score])
        );

        const mergedItems = items.map((item) => ({
          ...item,
          score: scoreMap.get(Number(item.id)) ?? undefined,
        }));

        mergedItems.sort((a, b) => (b.score ?? 0) - (a.score ?? 0));
        setRecommendations(mergedItems);
      }

      setShowRecommendations(true);
    } catch (err) {
      console.error("Failed to get recommendations:", err);
    } finally {
      setLoadingRecs(false);
    }
  };

  const handleGoToHome = () => {
    // Store preferences in localStorage for future use
    localStorage.setItem(
      "userPreferences",
      JSON.stringify(Array.from(selectedCategories))
    );
    navigate("/");
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-900 to-purple-900 flex items-center justify-center">
        <div className="text-white text-xl">Carregando...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 to-purple-900 p-8">
      <div className="max-w-6xl mx-auto">
        <AnimatePresence mode="wait">
          {!showRecommendations ? (
            <motion.div
              key="selection"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              {/* Header */}
              <div className="text-center mb-12">
                <motion.h1
                  initial={{ opacity: 0, y: -20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="text-4xl font-bold text-white mb-4"
                >
                  Bem-vindo ao Sistema de Recomendações!
                </motion.h1>
                <motion.p
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.2 }}
                  className="text-xl text-blue-200"
                >
                  Selecione as categorias que mais interessam você para receber
                  recomendações personalizadas
                </motion.p>
              </div>

              {/* Categories Grid */}
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 mb-8">
                {categories.map((category, index) => (
                  <motion.button
                    key={category.id}
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: index * 0.05 }}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => toggleCategory(category.id)}
                    className={`p-6 rounded-xl border-2 transition-all duration-200 ${
                      selectedCategories.has(category.id)
                        ? "bg-blue-500 border-blue-300 text-white shadow-lg shadow-blue-500/30"
                        : "bg-white/10 border-white/20 text-white hover:bg-white/20"
                    }`}
                  >
                    <div className="text-4xl mb-2">{category.icon}</div>
                    <div className="font-semibold text-sm">{category.name}</div>
                    <div className="text-xs mt-1 opacity-70">
                      {category.item_count} datasets
                    </div>
                  </motion.button>
                ))}
              </div>

              {/* Selected count and button */}
              <div className="text-center">
                <motion.p
                  animate={{ opacity: selectedCategories.size > 0 ? 1 : 0.5 }}
                  className="text-white mb-4"
                >
                  {selectedCategories.size > 0
                    ? `${selectedCategories.size} categoria(s) selecionada(s)`
                    : "Selecione pelo menos uma categoria"}
                </motion.p>
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={handleGetRecommendations}
                  disabled={selectedCategories.size === 0 || loadingRecs}
                  className={`px-8 py-4 rounded-full font-semibold text-lg transition-all ${
                    selectedCategories.size > 0
                      ? "bg-gradient-to-r from-blue-500 to-purple-500 text-white shadow-lg hover:shadow-xl"
                      : "bg-gray-500 text-gray-300 cursor-not-allowed"
                  }`}
                >
                  {loadingRecs ? "Gerando recomendações..." : "Ver Recomendações"}
                </motion.button>
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="recommendations"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              {/* Header */}
              <div className="text-center mb-8">
                <motion.h2
                  initial={{ opacity: 0, y: -20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="text-3xl font-bold text-white mb-2"
                >
                  Suas Recomendações Personalizadas
                </motion.h2>
                <p className="text-blue-200">
                  Baseado nas suas preferências:{" "}
                  {Array.from(selectedCategories)
                    .map((catId) => categories.find((c) => c.id === catId)?.name)
                    .filter(Boolean)
                    .join(", ")}
                </p>
              </div>

              {/* Recommendations Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 mb-8">
                {recommendations.map((item, index) => (
                  <motion.div
                    key={item.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                    whileHover={{ scale: 1.02, y: -5 }}
                    className="bg-white rounded-xl overflow-hidden shadow-lg"
                  >
                    <img
                      src={item.image_url || "/placeholder.png"}
                      alt={item.title}
                      className="w-full h-40 object-cover"
                    />
                    <div className="p-4">
                      <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2">
                        {item.title}
                      </h3>
                      <p className="text-sm text-gray-600 line-clamp-3">
                        {item.description}
                      </p>
                      {item.score !== undefined && (
                        <div className="mt-3 flex items-center">
                          <div className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
                            Score: {(item.score * 100).toFixed(0)}%
                          </div>
                        </div>
                      )}
                    </div>
                  </motion.div>
                ))}
              </div>

              {/* Action buttons */}
              <div className="flex justify-center gap-4">
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => setShowRecommendations(false)}
                  className="px-6 py-3 rounded-full font-semibold bg-white/20 text-white border border-white/30 hover:bg-white/30 transition-all"
                >
                  ← Alterar Preferências
                </motion.button>
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={handleGoToHome}
                  className="px-8 py-3 rounded-full font-semibold bg-gradient-to-r from-green-500 to-emerald-500 text-white shadow-lg hover:shadow-xl transition-all"
                >
                  Continuar para o Sistema →
                </motion.button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
