"use client";

import {
  GoogleAuthProvider,
  onAuthStateChanged,
  signInAnonymously,
  signInWithPopup,
  signOut as firebaseSignOut,
  type User,
} from "firebase/auth";
import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { firebaseAuth, isFirebaseConfigured } from "@/lib/firebase";
import { useAppStore } from "@/store/useAppStore";

type AuthContextValue = {
  user: User | null;
  signInWithGoogle: () => Promise<void>;
  signInAnonymously: () => Promise<void>;
  signOut: () => Promise<void>;
  isReady: boolean;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isReady, setIsReady] = useState(false);
  const setUserStore = useAppStore((state) => state.setUser);

  useEffect(() => {
    if (!firebaseAuth) {
      setIsReady(true);
      return;
    }

    const unsubscribe = onAuthStateChanged(firebaseAuth, (nextUser) => {
      setUser(nextUser);
      setUserStore(
        nextUser
          ? {
              uid: nextUser.uid,
              email: nextUser.email,
              displayName: nextUser.displayName,
            }
          : null,
      );
      setIsReady(true);
    });

    return () => unsubscribe();
  }, [setUserStore]);

  const signInWithGoogle = async () => {
    if (!firebaseAuth || !isFirebaseConfigured) {
      return;
    }

    const provider = new GoogleAuthProvider();
    await signInWithPopup(firebaseAuth, provider);
  };

  const signInAnonymouslyUser = async () => {
    if (!firebaseAuth || !isFirebaseConfigured) {
      return;
    }

    await signInAnonymously(firebaseAuth);
  };

  const signOut = async () => {
    if (!firebaseAuth) {
      return;
    }

    await firebaseSignOut(firebaseAuth);
  };

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      signInWithGoogle,
      signInAnonymously: signInAnonymouslyUser,
      signOut,
      isReady,
    }),
    [user, isReady],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }

  return context;
}
