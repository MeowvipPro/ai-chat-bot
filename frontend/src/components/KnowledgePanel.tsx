import { useEffect, useCallback, useRef } from "react";
import { useDropzone } from "react-dropzone";
import { useKnowledgeStore } from "../hooks/useKnowledge";
import {
  BookOpen,
  Upload,
  Trash2,
  FileText,
  Loader2,
  X,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import toast from "react-hot-toast";
import { useState } from "react";

export default function KnowledgePanel() {
  const { docs, loading, fetchDocs, uploadDoc, deleteDoc } =
    useKnowledgeStore();
  const [expanded, setExpanded] = useState(false);
  const [uploading, setUploading] = useState(false);
  const fetched = useRef(false);

  useEffect(() => {
    if (!fetched.current) {
      fetched.current = true;
      fetchDocs();
    }
  }, [fetchDocs]);

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      setUploading(true);
      try {
        for (const file of acceptedFiles) {
          await uploadDoc(file);
          toast.success(`${file.name} added to knowledge base`);
        }
      } catch {
        toast.error("Upload failed");
      } finally {
        setUploading(false);
      }
    },
    [uploadDoc]
  );

  const { getRootProps, getInputProps, isDragActive, open } = useDropzone({
    onDrop,
    noClick: true,
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
    maxSize: 50 * 1024 * 1024,
  });

  const handleDelete = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await deleteDoc(id);
      toast.success("Document removed");
    } catch {
      toast.error("Delete failed");
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div
      {...getRootProps()}
      className="border-t border-gray-200 dark:border-gray-800"
    >
      <input {...getInputProps()} />
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center gap-2 px-3 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition"
      >
        <BookOpen size={14} />
        <span className="flex-1 text-left">Knowledge Base</span>
        <span className="text-xs text-gray-400">{docs.length}</span>
        {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </button>

      {expanded && (
        <div className="px-2 pb-2 space-y-1.5">
          {/* Upload button */}
          <button
            onClick={open}
            disabled={uploading}
            className="flex w-full items-center gap-2 rounded-lg border border-dashed border-gray-300 dark:border-gray-700 px-3 py-2 text-xs text-gray-500 dark:text-gray-400 hover:border-indigo-400 hover:text-indigo-500 transition"
          >
            {uploading ? (
              <Loader2 size={12} className="animate-spin" />
            ) : (
              <Upload size={12} />
            )}
            Upload documents
          </button>

          {isDragActive && (
            <div className="rounded-lg border-2 border-dashed border-indigo-400 bg-indigo-50 dark:bg-indigo-950 p-3 text-center text-xs text-indigo-500">
              Drop files here...
            </div>
          )}

          {/* Document list */}
          {loading && docs.length === 0 ? (
            <div className="flex justify-center py-2">
              <Loader2 size={14} className="animate-spin text-gray-400" />
            </div>
          ) : docs.length === 0 ? (
            <p className="text-xs text-center text-gray-400 py-2">
              No documents yet
            </p>
          ) : (
            <div className="max-h-40 overflow-y-auto space-y-0.5">
              {docs.map((doc) => (
                <div
                  key={doc.id}
                  className="group flex items-center gap-1.5 rounded-md px-2 py-1.5 text-xs hover:bg-gray-100 dark:hover:bg-gray-800 transition"
                >
                  <FileText size={12} className="shrink-0 text-gray-400" />
                  <span className="flex-1 truncate text-gray-600 dark:text-gray-400">
                    {doc.filename}
                  </span>
                  <span className="shrink-0 text-gray-400 text-[10px]">
                    {formatSize(doc.file_size)}
                  </span>
                  {doc.processing_status !== "completed" && (
                    <span
                      className={`shrink-0 text-[10px] px-1 py-0.5 rounded ${
                        doc.processing_status === "failed"
                          ? "text-red-500"
                          : "text-yellow-500"
                      }`}
                    >
                      {doc.processing_status === "processing" ? (
                        <Loader2 size={10} className="animate-spin" />
                      ) : (
                        "failed"
                      )}
                    </span>
                  )}
                  <button
                    onClick={(e) => handleDelete(doc.id, e)}
                    className="shrink-0 opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 transition"
                  >
                    <Trash2 size={12} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
