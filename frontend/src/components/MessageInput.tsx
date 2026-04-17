import { useState, useRef } from "react";
import { useChatStore } from "../hooks/useChat";
import { Send, Paperclip } from "lucide-react";
import toast from "react-hot-toast";

interface Props {
  onFileUploadClick: () => void;
}

export default function MessageInput({ onFileUploadClick }: Props) {
  const [input, setInput] = useState("");
  const { sendMessage, streaming, activeChat, createChat } = useChatStore();
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault();
    const text = input.trim();
    if (!text || streaming) return;

    setInput("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }

    try {
      // Auto-create chat if none selected
      if (!activeChat) {
        await createChat(text.slice(0, 50));
      }
      await sendMessage(text);
    } catch {
      toast.error("Failed to send message");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    // Auto-resize
    const el = e.target;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 200) + "px";
  };

  return (
    <div className="border-t border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-950 px-4 py-3">
      <form
        onSubmit={handleSubmit}
        className="mx-auto flex max-w-3xl items-end gap-2"
      >
        <button
          type="button"
          onClick={onFileUploadClick}
          className="mb-1 rounded-lg p-2 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800 transition"
          title="Upload file"
        >
          <Paperclip size={18} />
        </button>
        <textarea
          ref={textareaRef}
          rows={1}
          value={input}
          onChange={handleTextareaChange}
          onKeyDown={handleKeyDown}
          placeholder="Type a message..."
          className="flex-1 resize-none rounded-xl border border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 px-4 py-2.5 text-sm text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none"
        />
        <button
          type="submit"
          disabled={!input.trim() || streaming}
          className="mb-1 rounded-lg bg-indigo-600 p-2.5 text-white hover:bg-indigo-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Send size={16} />
        </button>
      </form>
    </div>
  );
}
