import type React from "react"
import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { ThemeProvider } from "@/components/theme-provider"
import { ThemeCustomizer } from "@/components/theme-customizer"
import { LocaleProvider } from "@/lib/locale-context"
import { LanguageSwitcher } from "@/components/language-switcher"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "LLM Quality Observer Dashboard",
  description: "Monitor and evaluate LLM quality metrics in real-time",
  generator: 'v0.app'
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider attribute="class" defaultTheme="light" enableSystem={false} disableTransitionOnChange>
          <LocaleProvider>
            {children}
            <ThemeCustomizer />
            <div className="fixed right-4 top-4 z-[80] flex gap-2">
              <LanguageSwitcher />
            </div>
          </LocaleProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}
