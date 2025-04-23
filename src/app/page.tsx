import Header from "@/components/header";

export default function Home() {
  return (
    <>
    <Header />
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100 p-4">
      <h1 className="text-3xl font-bold mb-4">Legal Case Study Chat</h1>
      {/*<Chat />*/}
    </div>
    </>
  );
}
