"use client";

import { useState, ChangeEvent, FormEvent } from "react";

export default function ChatSummary() {
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

      reader.readAsText(file); // Assumes .txt; use other logic for PDF/DOCX
    }
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setResponse("");

    try {
      const payload = {
        document_text: fileContent,
      };

      const res = await fetch("https://rl-backend-legal-summarizer.onrender.com/summarize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error("Failed to fetch summary");

      const data = await res.json();
      setResponse(JSON.stringify(data.summary, null, 2));
    } catch (error) {
      console.error("Error:", error);
      setResponse("Error fetching summary");
    }

    setLoading(false);
  };

  return (
    <div className="flex flex-col items-center w-full max-w-4xl p-4 bg-white shadow-md rounded-lg">
      <form onSubmit={handleSubmit} className="w-full space-y-3">
        <label htmlFor="file-upload" className="block text-sm font-medium text-gray-700">
          Upload the Legal Document to summarize
        </label>
        <input
          id="file-upload"
          type="file"
          accept=".txt"
          onChange={handleFileChange}
          className="w-full border border-gray-300 rounded p-2"
          required
        />

        <button
          type="submit"
          className="w-full bg-blue-600 text-white py-2 rounded disabled:opacity-50"
          disabled={loading || !fileContent}
        >
          {loading ? "Summarizing..." : "Summarize"}
        </button>
      </form>

      {response && (
        <pre className="mt-4 p-2 bg-gray-200 border rounded w-full whitespace-pre-wrap">
          Summary: {response}
        </pre>
      )}
    </div>
  );
}
