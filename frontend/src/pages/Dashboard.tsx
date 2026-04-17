import { useState } from "react";
import Sidebar from "../components/Sidebar";
import ChatInterface from "../components/ChatInterface";
import FileUpload from "../components/FileUpload";

export default function Dashboard() {
  const [fileUploadOpen, setFileUploadOpen] = useState(false);

  return (
    <div className="flex h-screen bg-white dark:bg-gray-950">
      <Sidebar />
      <main className="flex flex-1 flex-col overflow-hidden">
        <ChatInterface onFileUploadClick={() => setFileUploadOpen(true)} />
      </main>
      <FileUpload open={fileUploadOpen} onClose={() => setFileUploadOpen(false)} />
    </div>
  );
}
