import type { Metadata } from "next"
import Content from "@/components/overview/content"
import Layout from "@/components/cmsfullform/layout"

export const metadata: Metadata = {
  title: "Overview - LLM Quality Observer",
  description: "Real-time monitoring of LLM quality metrics",
}

export default function HomePage() {
  return (
    <Layout>
      <Content />
    </Layout>
  )
}
