import type { Metadata } from "next"
import Content from "@/components/models/content"
import Layout from "@/components/cmsfullform/layout"

export const metadata: Metadata = {
  title: "Models - LLM Quality Observer",
  description: "Compare performance metrics across different LLM models",
}

export default function ModelsPage() {
  return (
    <Layout>
      <Content />
    </Layout>
  )
}
