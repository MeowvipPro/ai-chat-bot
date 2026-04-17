import { useEffect, useState } from "react";
import { useChatStore } from "../hooks/useChat";
import api from "../services/api";
import { ChevronDown } from "lucide-react";

interface Model {
  id: string;
  name: string;
  provider: string;
}

export default function ModelSelector() {
  const { activeChat, updateChat } = useChatStore();
  const [models, setModels] = useState<Model[]>([]);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    api
      .get<{ models: Model[] }>("/models/available")
      .then((res) => setModels(res.data.models))
      .catch(() => {});
  }, []);

  if (!activeChat) return null;

  const currentModel =
    models.find(
      (m) => m.id === activeChat.model_name && m.provider === activeChat.model_provider
    ) || { id: activeChat.model_name, name: activeChat.model_name, provider: activeChat.model_provider };

  const handleSelect = async (model: Model) => {
    await updateChat(activeChat.id, {
      model_provider: model.provider,
      model_name: model.id,
    });
    setOpen(false);
  };

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1 rounded-lg border border-gray-300 dark:border-gray-700 px-3 py-1.5 text-xs font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 transition"
      >
        <span className="capitalize">{currentModel.provider}</span>
        <span className="text-gray-400">/</span>
        <span>{currentModel.name}</span>
        <ChevronDown size={12} />
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-1 z-50 w-64 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 shadow-lg py-1">
          {models.map((model) => (
            <button
              key={`${model.provider}-${model.id}`}
              onClick={() => handleSelect(model)}
              className="w-full px-3 py-2 text-left text-sm hover:bg-gray-50 dark:hover:bg-gray-800 transition flex justify-between items-center"
            >
              <span className="text-gray-900 dark:text-white">{model.name}</span>
              <span className="text-xs text-gray-400 capitalize">{model.provider}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
