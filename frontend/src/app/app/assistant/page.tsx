"use client";

import { FormEvent, useState } from "react";

export default function AssistantPage() {
  const [message, setMessage] = useState("");
  const [sent, setSent] = useState<string[]>([]);

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (!message.trim()) return;
    setSent((current) => [...current, message.trim()]);
    setMessage("");
  };

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-4xl flex-col px-6 py-12">
      <a href="/" className="text-sm font-semibold text-emerald-700">NyayaAi</a>
      <h1 className="mt-8 text-4xl font-bold tracking-tight">Ask NyayaAi</h1>
      <p className="mt-3 text-slate-600">Ask a legal-information question. Include your state and the key dates or words from your document.</p>
      <div className="mt-8 flex-1 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="min-h-72 space-y-4">
          {sent.length === 0 ? (
            <p className="rounded-2xl bg-slate-50 p-4 text-slate-600">Your questions will appear here with source-backed answers and clear limitations.</p>
          ) : sent.map((item, index) => (
            <div key={`${item}-${index}`} className="ml-auto max-w-xl rounded-2xl bg-slate-900 p-4 text-white">{item}</div>
          ))}
        </div>
        <form onSubmit={submit} className="mt-8 flex gap-3">
          <label htmlFor="question" className="sr-only">Question</label>
          <input id="question" value={message} onChange={(event) => setMessage(event.target.value)} placeholder="What would you like to understand?" className="min-h-12 flex-1 rounded-xl border border-slate-300 px-4 outline-none focus:border-emerald-600" />
          <button type="submit" className="min-h-12 rounded-xl bg-emerald-700 px-5 font-semibold text-white hover:bg-emerald-800">Send</button>
        </form>
      </div>
    </main>
  );
}
