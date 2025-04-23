import Header from "@/components/header";

export default function Home() {
  return (
    <>
    <Header />
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100 p-4">
      <h1 className="text-3xl font-bold mb-4">Legal Case Study Chat</h1>
      <div className="flex flex-row flex-wrap justify-center gap-6">
          {/* Summarize Card */}
          <a href="/chat/summarizer" className="w-80 overflow-hidden rounded-lg shadow-sm bg-white transition hover:shadow-lg">
            <img
              alt="Summarize"
              src="https://blog.routinehub.co/content/images/size/w2000/2023/10/Tipo-de-Regimenes-Fiscales--3-.jpg"
              className="h-56 w-full object-cover"
            />
            <div className="p-4 sm:p-6">
              <h3 className="text-lg font-semibold text-gray-900">Summarize Cases</h3>
              <p className="mt-2 text-sm text-gray-600">
                Get concise summaries of lengthy legal documents with a single click.
              </p>
            </div>
          </a>

          {/* QnA Card */}
          <a href="/chat/qna" className="w-80 overflow-hidden rounded-lg shadow-sm bg-white transition hover:shadow-lg">
            <img
              alt="QnA"
              src="https://media.istockphoto.com/id/1337475990/photo/q-and-a-question-and-answer-shot-form-on-wooden-block.jpg?s=612x612&w=0&k=20&c=LrALcokTfC-1-1SD3WM1rgVYFIFu4TL7u47xlEeh2VQ="
              className="h-56 w-full object-cover"
            />
            <div className="p-4 sm:p-6">
              <h3 className="text-lg font-semibold text-gray-900">Ask Questions</h3>
              <p className="mt-2 text-sm text-gray-600">
                Ask natural language questions and receive contextual answers from case files.
              </p>
            </div>
          </a>

          {/* Retriever Card */}
          <a href="/chat/retriever" className="w-80 overflow-hidden rounded-lg shadow-sm bg-white transition hover:shadow-lg">
            <img
              alt="Retriever"
              src="https://static1.squarespace.com/static/564a53ace4b0ef1eb2daff41/t/6223c1857ffd5f50ae7bf4b9/1651199572372/Retrieve.jpg?format=1500w"
              className="h-56 w-full object-cover"
            />
            <div className="p-4 sm:p-6">
              <h3 className="text-lg font-semibold text-gray-900">Retrieve Similar Cases</h3>
              <p className="mt-2 text-sm text-gray-600">
                Find legal cases similar to your uploaded document using smart retrieval.
              </p>
            </div>
          </a>
        </div>

      {/*<Chat />*/}
    </div>
    </>
  );
}
