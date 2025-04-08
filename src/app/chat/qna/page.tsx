import ChatQNA from "@/app/chat/qna/chat_qna";
import Header from "@/components/header";

export default function QnaPage() {
  return (
    <>
      <Header />
      <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100 p-4">
        <h1 className="text-3xl font-bold mb-4">Legal Question and Answers</h1>
        <ChatQNA />
      </div>
    </>
  );
}
