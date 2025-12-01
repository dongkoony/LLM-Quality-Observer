"use client"

import { Languages } from "lucide-react"
import { useLocale, Locale } from "@/lib/locale-context"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

const languages = [
  { code: "en" as Locale, name: "English", flag: "🇺🇸" },
  { code: "ko" as Locale, name: "한국어", flag: "🇰🇷" },
  { code: "ja" as Locale, name: "日本語", flag: "🇯🇵" },
  { code: "zh" as Locale, name: "中文", flag: "🇨🇳" },
]

export function LanguageSwitcher() {
  const { locale, setLocale } = useLocale()

  const currentLanguage = languages.find((lang) => lang.code === locale) || languages[0]

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="h-9 w-9 rounded-full"
          title="Change Language"
        >
          <Languages className="h-4 w-4" />
          <span className="sr-only">Change language</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-40">
        {languages.map((lang) => (
          <DropdownMenuItem
            key={lang.code}
            onClick={() => setLocale(lang.code)}
            className={locale === lang.code ? "bg-accent" : ""}
          >
            <span className="mr-2">{lang.flag}</span>
            <span>{lang.name}</span>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
