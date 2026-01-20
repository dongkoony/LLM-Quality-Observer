"use client"

import { createContext, useContext, useState, useEffect, ReactNode } from "react"

export type Locale = "en" | "ko" | "ja" | "zh"

interface LocaleContextType {
  locale: Locale
  setLocale: (locale: Locale) => void
}

const LocaleContext = createContext<LocaleContextType | undefined>(undefined)

export function LocaleProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("en")

  // Load locale from localStorage on mount
  useEffect(() => {
    const savedLocale = localStorage.getItem("locale") as Locale | null
    if (savedLocale && ["en", "ko", "ja", "zh"].includes(savedLocale)) {
      setLocaleState(savedLocale)
    }
  }, [])

  // Save locale to localStorage when it changes
  const setLocale = (newLocale: Locale) => {
    setLocaleState(newLocale)
    localStorage.setItem("locale", newLocale)
  }

  return (
    <LocaleContext.Provider value={{ locale, setLocale }}>
      {children}
    </LocaleContext.Provider>
  )
}

export function useLocale() {
  const context = useContext(LocaleContext)
  if (context === undefined) {
    throw new Error("useLocale must be used within a LocaleProvider")
  }
  return context
}
