import { useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { useChatStore } from "../hooks/useChat";
import { Bot, User } from "lucide-react";
import clsx from "clsx";

export default function MessageList() {
  const { messages, streaming, streamContent } = useChatStore();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamContent]);

  if (messages.length === 0 && !streaming) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <div className="text-center text-gray-400 dark:text-gray-600">
          <Bot size={48} className="mx-auto mb-4" />
          <p className="text-lg font-medium">How can I help you today?</p>
          <p className="text-sm mt-1">Send a message to start chatting</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6">
      {messages.map((msg, idx) => (
        <div
          key={idx}
          className={clsx("flex gap-3 max-w-3xl mx-auto", {
            "flex-row-reverse": msg.role === "user",
          })}
        >
          <div
            className={clsx(
              "flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
              msg.role === "user"
                ? "bg-indigo-100 dark:bg-indigo-900"
                : "bg-emerald-100 dark:bg-emerald-900"
            )}
          >
            {msg.role === "user" ? (
              <User size={16} className="text-indigo-600 dark:text-indigo-400" />
            ) : (
              <Bot size={16} className="text-emerald-600 dark:text-emerald-400" />
            )}
          </div>
          <div
            className={clsx(
              "rounded-2xl px-4 py-3 text-sm leading-relaxed max-w-[80%]",
              msg.role === "user"
                ? "bg-indigo-600 text-white"
                : "bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100"
            )}
          >
            {msg.role === "assistant" ? (
              <div className="prose dark:prose-invert prose-sm max-w-none">
                <ReactMarkdown>{msg.content}</ReactMarkdown>
              </div>
            ) : (
              msg.content
            )}
          </div>
        </div>
      ))}

      {/* Streaming indicator */}
      {streaming && (
        <div className="flex gap-3 max-w-3xl mx-auto">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-emerald-100 dark:bg-emerald-900">
            <Bot size={16} className="text-emerald-600 dark:text-emerald-400" />
          </div>
          <div className="rounded-2xl px-4 py-3 text-sm leading-relaxed bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 max-w-[80%]">
            {streamContent ? (
              <div className="prose dark:prose-invert prose-sm max-w-none">
                <ReactMarkdown>{streamContent}</ReactMarkdown>
              </div>
            ) : (
              <div className="flex gap-1">
                <span className="animate-bounce">●</span>
                <span className="animate-bounce" style={{ animationDelay: "0.1s" }}>●</span>
                <span className="animate-bounce" style={{ animationDelay: "0.2s" }}>●</span>
              </div>
            )}
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}
