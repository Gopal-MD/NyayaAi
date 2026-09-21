"use client";

import { ChangeEvent, useState } from "react";

const accepted = ".pdf,.docx,.jpg,.jpeg,.png";

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [consent, setConsent] = useState(false);
  const [status, setStatus] = useState("");

  const chooseFile = (event: ChangeEvent<HTMLInputElement>) => {
    setFile(event.target.files?.[0] ?? null);
    setStatus("");
  };

  const upload = async () => {
    if (!file || !consent) {
      setStatus("Choose a document and accept the consent statement first.");
      return;
    }

    const form = new FormData();
    form.append("file", file);
    form.append("case_id", "demo-case");
    form.append("consent_accepted", "true");
    setStatus("Upload is ready. Sign in and connect a case to send it to the API.");
    void form;
  };

  return (
    <main className="mx-auto min-h-screen w-full max-w-3xl px-6 py-12">
      <a href="/" className="text-sm font-semibold text-emerald-700">NyayaAi</a>
      <h1 className="mt-8 text-4xl font-bold tracking-tight">Review a document</h1>
      <p className="mt-3 text-slate-600">Upload a rental agreement to extract facts, deadlines, and clauses that deserve a closer look.</p>
      <section className="mt-8 rounded-3xl border border-dashed border-slate-300 bg-white p-8 shadow-sm">
        <label htmlFor="document" className="block cursor-pointer rounded-2xl border border-slate-200 bg-slate-50 p-8 text-center hover:bg-slate-100">
          <span className="block text-lg font-semibold">Choose PDF, DOCX, JPG, or PNG</span>
          <span className="mt-2 block text-sm text-slate-500">Maximum file size: 10 MB</span>
          <input id="document" type="file" accept={accepted} onChange={chooseFile} className="sr-only" />
        </label>
        {file && <p className="mt-4 text-sm text-slate-700">Selected: {file.name}</p>}
        <label className="mt-6 flex min-h-12 items-start gap-3 text-sm text-slate-600">
          <input type="checkbox" checked={consent} onChange={(event) => setConsent(event.target.checked)} className="mt-1 h-5 w-5" />
          <span>I understand that documents are processed to provide legal information, and that NyayaAi is not a substitute for a lawyer.</span>
        </label>
        <button type="button" onClick={upload} className="mt-6 min-h-12 w-full rounded-xl bg-slate-900 px-5 font-semibold text-white hover:bg-slate-700">Upload document</button>
        {status && <p role="status" className="mt-4 text-sm text-slate-600">{status}</p>}
      </section>
    </main>
  );
}
