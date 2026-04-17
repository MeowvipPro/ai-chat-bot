import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import api from "../services/api";
import { useChatStore } from "../hooks/useChat";
import { Upload, X, FileText, Loader2 } from "lucide-react";
import toast from "react-hot-toast";

interface UploadedFile {
  id: number;
  filename: string;
  processing_status: string;
}

interface Props {
  open: boolean;
  onClose: () => void;
}

export default function FileUpload({ open, onClose }: Props) {
  const { activeChat } = useChatStore();
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [uploading, setUploading] = useState(false);
  const [qaQuestion, setQaQuestion] = useState("");
  const [qaAnswer, setQaAnswer] = useState("");
  const [qaLoading, setQaLoading] = useState(false);
  const [selectedFileId, setSelectedFileId] = useState<number | null>(null);

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      if (acceptedFiles.length === 0) return;
      setUploading(true);
      try {
        for (const file of acceptedFiles) {
          const formData = new FormData();
          formData.append("file", file);
          if (activeChat) {
            formData.append("chat_id", String(activeChat.id));
          }
          const res = await api.post<UploadedFile>("/files/upload", formData, {
            headers: { "Content-Type": "multipart/form-data" },
          });
          setFiles((prev) => [...prev, res.data]);
          toast.success(`${file.name} uploaded`);
        }
      } catch {
        toast.error("Upload failed");
      } finally {
        setUploading(false);
      }
    },
    [activeChat]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "text/plain": [".txt"],
      "image/png": [".png"],
      "image/jpeg": [".jpg", ".jpeg"],
      "application/msword": [".doc"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
      "application/vnd.ms-excel": [".xls"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
    },
    maxSize: 50 * 1024 * 1024, // 50MB
  });

  const handleQA = async () => {
    if (!selectedFileId || !qaQuestion.trim()) return;
    setQaLoading(true);
    setQaAnswer("");
    try {
      const res = await api.post<{ answer: string; sources: string[] }>(
        `/files/${selectedFileId}/qa`,
        { question: qaQuestion }
      );
      setQaAnswer(res.data.answer);
    } catch {
      toast.error("Q&A failed. File may still be processing.");
    } finally {
      setQaLoading(false);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-lg rounded-2xl bg-white dark:bg-gray-900 p-6 shadow-2xl mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            File Upload & Q&A
          </h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
          >
            <X size={20} />
          </button>
        </div>

        {/* Dropzone */}
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition ${
            isDragActive
              ? "border-indigo-500 bg-indigo-50 dark:bg-indigo-950"
              : "border-gray-300 dark:border-gray-700 hover:border-gray-400"
          }`}
        >
          <input {...getInputProps()} />
          {uploading ? (
            <Loader2 size={24} className="mx-auto animate-spin text-indigo-500" />
          ) : (
            <>
              <Upload size={24} className="mx-auto text-gray-400 mb-2" />
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Drop PDF, text, or image files here, or click to browse
              </p>
            </>
          )}
        </div>

        {/* Uploaded files list */}
        {files.length > 0 && (
          <div className="mt-4 space-y-2">
            <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Uploaded Files
            </h3>
            {files.map((f) => (
              <div
                key={f.id}
                onClick={() => setSelectedFileId(f.id)}
                className={`flex items-center gap-2 rounded-lg p-2 text-sm cursor-pointer transition ${
                  selectedFileId === f.id
                    ? "bg-indigo-50 dark:bg-indigo-950 border border-indigo-300 dark:border-indigo-700"
                    : "hover:bg-gray-50 dark:hover:bg-gray-800"
                }`}
              >
                <FileText size={14} className="text-gray-400" />
                <span className="flex-1 truncate text-gray-700 dark:text-gray-300">
                  {f.filename}
                </span>
                <span
                  className={`text-xs px-2 py-0.5 rounded-full ${
                    f.processing_status === "completed"
                      ? "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300"
                      : f.processing_status === "failed"
                        ? "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300"
                        : "bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300"
                  }`}
                >
                  {f.processing_status}
                </span>
              </div>
            ))}
          </div>
        )}

        {/* Q&A section */}
        {selectedFileId && (
          <div className="mt-4 space-y-2">
            <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Ask about this file
            </h3>
            <div className="flex gap-2">
              <input
                type="text"
                value={qaQuestion}
                onChange={(e) => setQaQuestion(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleQA()}
                placeholder="Ask a question about the file..."
                className="flex-1 rounded-lg border border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white outline-none focus:ring-2 focus:ring-indigo-500"
              />
              <button
                onClick={handleQA}
                disabled={qaLoading || !qaQuestion.trim()}
                className="rounded-lg bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-700 disabled:opacity-50 transition"
              >
                {qaLoading ? "..." : "Ask"}
              </button>
            </div>
            {qaAnswer && (
              <div className="rounded-lg bg-gray-50 dark:bg-gray-800 p-3 text-sm text-gray-700 dark:text-gray-300">
                {qaAnswer}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
