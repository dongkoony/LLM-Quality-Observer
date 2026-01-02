import { en } from "./en"
import { ko } from "./ko"
import { ja } from "./ja"
import { zh } from "./zh"
import { Locale } from "@/lib/locale-context"

export const translations = {
  en,
  ko,
  ja,
  zh,
}

export function getTranslations(locale: Locale) {
  return translations[locale]
}
