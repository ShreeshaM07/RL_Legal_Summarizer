import ChatSummary from "@/app/chat/summarizer/chat_summarize";
import Header from "@/components/header";

export default function SummaryPage() {
  return (
    <>
      <Header />
      <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100 p-4">
        <h1 className="text-3xl font-bold mb-4">Legal Summary</h1>
        <ChatSummary />
      </div>
    </>
  );
}
