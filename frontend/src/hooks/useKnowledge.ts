import { create } from "zustand";
import api from "../services/api";

export interface KnowledgeDoc {
  id: number;
  filename: string;
  file_type: string;
  file_size: number;
  processing_status: string;
  is_knowledge: boolean;
  created_at: string;
}

interface KnowledgeStore {
  docs: KnowledgeDoc[];
  loading: boolean;
  fetchDocs: () => Promise<void>;
  uploadDoc: (file: File) => Promise<void>;
  deleteDoc: (id: number) => Promise<void>;
}

export const useKnowledgeStore = create<KnowledgeStore>((set) => ({
  docs: [],
  loading: false,

  fetchDocs: async () => {
    set({ loading: true });
    try {
      const res = await api.get<KnowledgeDoc[]>("/knowledge/");
      set({ docs: res.data });
    } finally {
      set({ loading: false });
    }
  },

  uploadDoc: async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    const res = await api.post<KnowledgeDoc>("/knowledge/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    set((state) => ({ docs: [res.data, ...state.docs] }));

    // Poll for processing completion
    const docId = res.data.id;
    const poll = setInterval(async () => {
      try {
        const updated = await api.get<KnowledgeDoc[]>("/knowledge/");
        const doc = updated.data.find((d) => d.id === docId);
        if (doc && doc.processing_status !== "processing") {
          clearInterval(poll);
          set({ docs: updated.data });
        }
      } catch {
        clearInterval(poll);
      }
    }, 2000);
    // Safety: stop polling after 2 minutes
    setTimeout(() => clearInterval(poll), 120000);
  },

  deleteDoc: async (id: number) => {
    await api.delete(`/knowledge/${id}`);
    set((state) => ({ docs: state.docs.filter((d) => d.id !== id) }));
  },
}));
