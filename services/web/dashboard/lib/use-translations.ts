"use client"

import { useLocale } from "./locale-context"
import { getTranslations } from "@/locales"

export function useTranslations() {
  const { locale } = useLocale()
  return getTranslations(locale)
}
