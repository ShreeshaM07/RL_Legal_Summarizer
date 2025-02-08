import ChatRetriever from "@/app/chat/chat_window";
import Header from "@/components/header";

export default function RetrieverPage() {
  return (
    <>
      <Header />
      <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100 p-4">
        <h1 className="text-3xl font-bold mb-4">Retriever Chat</h1>
        <ChatRetriever />
      </div>
    </>
  );
}
