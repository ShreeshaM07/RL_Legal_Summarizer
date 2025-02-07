"use client"; // This makes it a Client Component in Next.js

import { useState } from "react";

export default function Chat() {
  const [question, setQuestion] = useState<string>("");
  const [response, setResponse] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setResponse("");

    try {
      const res = await fetch("/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });

      if (!res.ok) throw new Error("Failed to fetch response");

      const data = await res.json();
      setResponse(data.answer || "No response");
    } catch (error) {
      console.error("Error:", error);
      setResponse("Error fetching response");
    }
    setLoading(false);
  };

  return (
    <div className="flex flex-col items-center w-full max-w-md p-4 bg-white shadow-md rounded-lg">
      <form onSubmit={handleSubmit} className="w-full">
        <input
          type="text"
          className="p-2 border border-gray-300 rounded w-full mb-2"
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
        <p className="mt-4 p-2 bg-gray-200 border rounded w-full">Response: {response}</p>
      )}
    </div>
  );
}
