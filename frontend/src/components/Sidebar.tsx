import { useEffect, useState } from "react";
import { useChatStore } from "../hooks/useChat";
import { useAuth } from "../context/AuthContext";
import { Plus, Trash2, MessageSquare, LogOut } from "lucide-react";
import clsx from "clsx";
import KnowledgePanel from "./KnowledgePanel";

export default function Sidebar() {
  const { chats, activeChat, fetchChats, createChat, selectChat, deleteChat } =
    useChatStore();
  const { user, logout } = useAuth();
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    if (!loaded) {
      fetchChats().then(() => setLoaded(true));
    }
  }, [fetchChats, loaded]);

  const handleNew = async () => {
    await createChat();
  };

  return (
    <aside className="flex h-full w-64 flex-col border-r border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900">
      {/* New chat button */}
      <div className="p-3">
        <button
          onClick={handleNew}
          className="flex w-full items-center gap-2 rounded-lg border border-gray-300 dark:border-gray-700 px-3 py-2.5 text-sm hover:bg-gray-100 dark:hover:bg-gray-800 transition"
        >
          <Plus size={16} />
          New Chat
        </button>
      </div>

      {/* Chat list */}
      <div className="flex-1 overflow-y-auto px-2 space-y-0.5">
        {chats.map((chat) => (
          <div
            key={chat.id}
            onClick={() => selectChat(chat.id)}
            className={clsx(
              "group flex items-center gap-2 rounded-lg px-3 py-2 text-sm cursor-pointer transition",
              activeChat?.id === chat.id
                ? "bg-indigo-50 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300"
                : "hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300"
            )}
          >
            <MessageSquare size={14} className="shrink-0" />
            <span className="flex-1 truncate">{chat.title}</span>
            <button
              onClick={(e) => {
                e.stopPropagation();
                deleteChat(chat.id);
              }}
              className="opacity-0 group-hover:opacity-100 hover:text-red-500 transition"
            >
              <Trash2 size={14} />
            </button>
          </div>
        ))}
      </div>

      {/* Knowledge Base */}
      <KnowledgePanel />

      {/* User section */}
      <div className="border-t border-gray-200 dark:border-gray-800 p-3">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600 dark:text-gray-400 truncate">
            {user?.username}
          </span>
          <button
            onClick={logout}
            className="text-gray-500 hover:text-red-500 transition"
            title="Logout"
          >
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </aside>
  );
}
