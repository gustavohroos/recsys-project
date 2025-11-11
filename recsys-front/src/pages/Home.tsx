import { useEffect, useState } from "react";
import type { Topic } from "../types/Topic";
import UserCard from "../components/UserCard";

export default function Home() {
  const [topics, setTopics] = useState<Topic[]>([]);
  const [selectedTopic, setSelectedTopic] = useState<Topic | null>(null);

  useEffect(() => {
    const mockedData: Topic[] = [
      {
        id: "1",
        title: "Introdução a Redes Neurais",
        description: "Conceitos básicos sobre redes neurais artificiais.",
        image:
          "https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?auto=format&fit=crop&w=300&q=80",
        score: 0.95,
      },
      {
        id: "2",
        title: "Sistemas de Recomendação",
        description: "CF, conteúdo, híbridos e métricas de avaliação.",
        image:
          "https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?auto=format&fit=crop&w=300&q=80",
        score: 0.87,
      },
      {
        id: "3",
        title: "Transformers",
        description: "Arquitetura, atenção, embeddings e aplicações.",
        image:
          "https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?auto=format&fit=crop&w=300&q=80",
        score: 0.89,
      },
    ];

    setTimeout(() => {
      setTopics(mockedData);
    }, 400);
  }, []);

return (
  <div className="w-full min-h-screen bg-gray-800 flex">

    {/* COLUNA 1 — USUÁRIO */}
    <div className="w-72 min-h-screen p-6 bg-gray-900 flex items-start justify-center">
      <UserCard
        name="User"
        email="ulian@empresa.com"
        role="X"
        avatarUrl="https://i.pravatar.cc/150?img=65"
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
              {topics.map((topic) => (
                <li key={topic.id}>
                  <button
                    onClick={() => setSelectedTopic(topic)}
                    className={`w-full text-left p-4 rounded-lg border transition hover:shadow ${
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
                  </button>
                </li>
              ))}
            </ul>
          </div>



          {/* DETALHES DO TÓPICO */}
          <div className="w-2/3 p-8 bg-white">
            {!selectedTopic ? (
              <p className="text-gray-500 text-center mt-20">
                Selecione um tópico na lista à esquerda.
              </p>
            ) : (
              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">
                  {selectedTopic.title}
                </h2>

                <img
                  src={selectedTopic.image}
                  alt={selectedTopic.title}
                  className="w-64 h-64 rounded-xl object-cover shadow mb-6"
                />

                <p className="text-gray-700 leading-relaxed">
                  {selectedTopic.description}
                </p>

                <div className="mt-4 text-sm text-gray-600">
                  Score: <strong>{selectedTopic.score}</strong>
                </div>
              </div>
            )}
          </div>

        </div>
      </div>
    </div>



    {/* COLUNA 3 — RELACIONADOS */}
    <div className="w-80 min-h-screen p-6 bg-gray-900 text-white">
      <h1 className="text-xl font-semibold mb-4">Relacionados</h1>

      {!selectedTopic ? (
        <p className="text-gray-400 text-sm">
          Selecione um tópico para ver os relacionados.
        </p>
      ) : (
        <ul className="flex flex-col gap-3">
          {topics.map((related) => (
            <li key={related.id}>
              <button
                onClick={() =>
                  setSelectedTopic({
                    ...selectedTopic,
                    title: related.title,
                  })
                }
                className="w-full text-left p-4 rounded-lg bg-gray-800 border border-gray-700 hover:bg-gray-700 transition"
              >
                <div className="flex items-center gap-3">
                  <img
                    src={related.image}
                    alt={related.title}
                    className="w-10 h-10 rounded-lg object-cover"
                  />
                  <span className="text-sm">{related.title}</span>
                </div>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>

  </div>
);
}
