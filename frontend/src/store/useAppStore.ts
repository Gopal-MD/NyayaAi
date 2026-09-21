import { create } from "zustand";

type User = {
  uid: string;
  email?: string | null;
  displayName?: string | null;
};

type AppState = {
  language: "en" | "ta";
  currentCaseId: string | null;
  user: User | null;
  setLanguage: (language: "en" | "ta") => void;
  setCurrentCaseId: (caseId: string | null) => void;
  setUser: (user: User | null) => void;
};

export const useAppStore = create<AppState>((set) => ({
  language: "en",
  currentCaseId: null,
  user: null,
  setLanguage: (language) => set({ language }),
  setCurrentCaseId: (currentCaseId) => set({ currentCaseId }),
  setUser: (user) => set({ user }),
}));
