import { create } from "zustand";
import api, { API_BASE } from "../services/api";

export interface ChatMessage {
  id?: number;
  chat_id?: number;
  role: "user" | "assistant";
  content: string;
  created_at?: string;
}

export interface Chat {
  id: number;
  title: string;
  model_provider: string;
  model_name: string;
  created_at: string;
  updated_at?: string;
  messages?: ChatMessage[];
}

interface ChatStore {
  chats: Chat[];
  activeChat: Chat | null;
  messages: ChatMessage[];
  streaming: boolean;
  streamContent: string;
  useKnowledge: boolean;

  fetchChats: () => Promise<void>;
  createChat: (
    title?: string,
    model_provider?: string,
    model_name?: string
  ) => Promise<Chat>;
  selectChat: (chatId: number) => Promise<void>;
  deleteChat: (chatId: number) => Promise<void>;
  updateChat: (
    chatId: number,
    data: { title?: string; model_provider?: string; model_name?: string }
  ) => Promise<void>;
  sendMessage: (content: string) => Promise<void>;
  setStreamContent: (content: string) => void;
  toggleKnowledge: () => void;
}

export const useChatStore = create<ChatStore>((set, get) => ({
  chats: [],
  activeChat: null,
  messages: [],
  streaming: false,
  streamContent: "",
  useKnowledge: false,

  fetchChats: async () => {
    const res = await api.get<Chat[]>("/chats/");
    set({ chats: res.data });
  },

  createChat: async (title, model_provider, model_name) => {
    const res = await api.post<Chat>("/chats/", {
      title: title || "New Chat",
      model_provider: model_provider || "openai",
      model_name: model_name || "gpt-3.5-turbo",
    });
    const chat = res.data;
    set((state) => ({ chats: [chat, ...state.chats], activeChat: chat, messages: [] }));
    return chat;
  },

  selectChat: async (chatId) => {
    const res = await api.get<Chat>(`/chats/${chatId}`);
    set({ activeChat: res.data, messages: res.data.messages || [] });
  },

  deleteChat: async (chatId) => {
    await api.delete(`/chats/${chatId}`);
    set((state) => {
      const chats = state.chats.filter((c) => c.id !== chatId);
      const activeChat = state.activeChat?.id === chatId ? null : state.activeChat;
      return {
        chats,
        activeChat,
        messages: activeChat ? state.messages : [],
      };
    });
  },

  updateChat: async (chatId, data) => {
    const res = await api.put<Chat>(`/chats/${chatId}`, data);
    set((state) => ({
      chats: state.chats.map((c) => (c.id === chatId ? { ...c, ...res.data } : c)),
      activeChat: state.activeChat?.id === chatId ? { ...state.activeChat, ...res.data } : state.activeChat,
    }));
  },

  sendMessage: async (content) => {
    const { activeChat, useKnowledge } = get();
    if (!activeChat) return;

    const userMsg: ChatMessage = { role: "user", content };
    set((state) => ({
      messages: [...state.messages, userMsg],
      streaming: true,
      streamContent: "",
    }));

    try {
      const token = localStorage.getItem("access_token");
      const response = await fetch(`${API_BASE}/chats/${activeChat.id}/messages`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ content, stream: true, use_knowledge: useKnowledge }),
      });

      if (!response.ok) throw new Error("Failed to send message");

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let full = "";

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const text = decoder.decode(value, { stream: true });
          const lines = text.split("\n");

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const data = JSON.parse(line.slice(6));
                if (data.token) {
                  full += data.token;
                  set({ streamContent: full });
                }
                if (data.done) {
                  break;
                }
                if (data.error) {
                  console.error("Stream error:", data.error);
                  break;
                }
              } catch {
                // skip malformed JSON
              }
            }
          }
        }
      }

      const assistantMsg: ChatMessage = { role: "assistant", content: full };
      set((state) => ({
        messages: [...state.messages, assistantMsg],
        streaming: false,
        streamContent: "",
      }));
    } catch (error) {
      set({ streaming: false, streamContent: "" });
      throw error;
    }
  },

  setStreamContent: (content) => set({ streamContent: content }),

  toggleKnowledge: () => set((state) => ({ useKnowledge: !state.useKnowledge })),
}));
