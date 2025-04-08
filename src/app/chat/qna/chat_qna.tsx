"use client";

import { useState, ChangeEvent, FormEvent } from "react";

export default function Chat() {
  const [question, setQuestion] = useState<string>("");
  const [response, setResponse] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [fileContent, setFileContent] = useState<string>("");

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();

      reader.onload = (event) => {
        const text = event.target?.result as string;
        setFileContent(text);
      };

      reader.readAsText(file); // For PDF or DOCX, you'll need another method
    }
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setResponse("");

    try {
      const payload = {
        query: question,
        document_text: fileContent,
      };

      const res = await fetch("http://localhost:8000/qna", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error("Failed to fetch response");

      const data = await res.json();
      setResponse(JSON.stringify(data.response, null, 2));
    } catch (error) {
      console.error("Error:", error);
      setResponse("Error fetching response");
    }

    setLoading(false);
  };

  return (
    <div className="flex flex-col items-center w-full max-w-md p-4 bg-white shadow-md rounded-lg">
      <form onSubmit={handleSubmit} className="w-full space-y-3">
        {"Upload the Legal Document to process"}
        <input
          type="file"
          accept=".txt" // PDF/DOCX not supported via readAsText()
          onChange={handleFileChange}
          className="w-full border border-gray-300 rounded p-2"
        />

        <input
          type="text"
          className="p-2 border border-gray-300 rounded w-full"
          placeholder="Type your legal question..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          required
        />

        <button
          type="submit"
          className="w-full bg-blue-600 text-white py-2 rounded disabled:opacity-50"
          disabled={loading}
        >
          {loading ? "Thinking..." : "Ask"}
        </button>
      </form>

      {response && (
        <pre className="mt-4 p-2 bg-gray-200 border rounded w-full whitespace-pre-wrap">
          Response: {response}
        </pre>
      )}
    </div>
  );
}
