import { useChatStore } from "../hooks/useChat";
import ModelSelector from "./ModelSelector";
import ThemeToggle from "./ThemeToggle";
import MessageList from "./MessageList";
import MessageInput from "./MessageInput";
import { BookOpen } from "lucide-react";

interface Props {
  onFileUploadClick: () => void;
}

export default function ChatInterface({ onFileUploadClick }: Props) {
  const { activeChat, useKnowledge, toggleKnowledge } = useChatStore();

  return (
    <div className="flex flex-1 flex-col h-full">
      {/* Header */}
      <header className="flex items-center justify-between border-b border-gray-200 dark:border-gray-800 px-4 py-2.5">
        <h2 className="text-sm font-medium text-gray-700 dark:text-gray-300 truncate">
          {activeChat?.title || "Generative AI Chat"}
        </h2>
        <div className="flex items-center gap-2">
          {/* Knowledge Base (RAG) Toggle */}
          <button
            onClick={toggleKnowledge}
            title={useKnowledge ? "Knowledge Base: ON" : "Knowledge Base: OFF"}
            className={`flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium transition ${
              useKnowledge
                ? "bg-indigo-100 text-indigo-700 dark:bg-indigo-900 dark:text-indigo-300 ring-1 ring-indigo-300 dark:ring-indigo-700"
                : "text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800 dark:text-gray-400"
            }`}
          >
            <BookOpen size={14} />
            <span>RAG</span>
            <span
              className={`inline-block h-2 w-2 rounded-full ${
                useKnowledge ? "bg-indigo-500" : "bg-gray-400"
              }`}
            />
          </button>
          <ModelSelector />
          <ThemeToggle />
        </div>
      </header>

      {/* Messages */}
      <MessageList />

      {/* Input */}
      <MessageInput onFileUploadClick={onFileUploadClick} />
    </div>
  );
}
