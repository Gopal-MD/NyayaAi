"use client";

import { useAppStore } from "@/store/useAppStore";

export default function Home() {
  const { language, setLanguage } = useAppStore();

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-6xl flex-col justify-center px-6 py-16">
      <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm sm:p-10">
        <div className="mb-8 flex items-center justify-between gap-3">
          <div>
            <p className="text-sm font-medium uppercase tracking-[0.2em] text-emerald-700">
              NyayaAi
            </p>
            <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900 sm:text-5xl">
              AI legal assistance for Tamil Nadu & beyond
            </h1>
          </div>

          <div className="inline-flex rounded-full border border-slate-200 bg-slate-50 p-1">
            <button
              type="button"
              onClick={() => setLanguage("en")}
              className={`rounded-full px-3 py-1.5 text-sm font-medium transition ${
                language === "en" ? "bg-slate-900 text-white" : "text-slate-600"
              }`}
            >
              EN
            </button>
            <button
              type="button"
              onClick={() => setLanguage("ta")}
              className={`rounded-full px-3 py-1.5 text-sm font-medium transition ${
                language === "ta" ? "bg-slate-900 text-white" : "text-slate-600"
              }`}
            >
              TA
            </button>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-[1.3fr_0.7fr]">
          <section className="space-y-5">
            <p className="max-w-2xl text-lg text-slate-600">
              Ask about tenancy rights, compare legal documents, upload evidence, and get guided action plans grounded in available legal sources.
            </p>

            <div className="flex flex-wrap gap-3">
              <a href="/app/assistant" className="inline-flex min-h-12 items-center rounded-xl bg-slate-900 px-5 font-semibold text-white hover:bg-slate-700">
                Ask a question
              </a>
              <a href="/app/upload" className="inline-flex min-h-12 items-center rounded-xl border border-slate-300 px-5 font-semibold text-slate-800 hover:bg-slate-50">
                Upload a document
              </a>
            </div>

            <div className="grid gap-4 sm:grid-cols-3">
              <div className="rounded-2xl bg-emerald-50 p-4">
                <p className="text-sm text-emerald-700">Document review</p>
                <p className="mt-2 text-2xl font-semibold">PDF + DOCX</p>
              </div>
              <div className="rounded-2xl bg-amber-50 p-4">
                <p className="text-sm text-amber-700">Search</p>
                <p className="mt-2 text-2xl font-semibold">RAG</p>
              </div>
              <div className="rounded-2xl bg-sky-50 p-4">
                <p className="text-sm text-sky-700">Support</p>
                <p className="mt-2 text-2xl font-semibold">Aid</p>
              </div>
            </div>
          </section>

          <aside className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
            <h2 className="text-lg font-semibold text-slate-900">Current session</h2>
            <ul className="mt-4 space-y-3 text-sm text-slate-600">
              <li>Language: {language === "en" ? "English" : "Tamil"}</li>
              <li>Case: {useAppStore.getState().currentCaseId ?? "Not started"}</li>
              <li>Auth: {useAppStore.getState().user ? "Signed in" : "Guest"}</li>
            </ul>
          </aside>
        </div>
      </div>
    </main>
  );
}
