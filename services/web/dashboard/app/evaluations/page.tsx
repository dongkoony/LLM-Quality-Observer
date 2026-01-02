import type { Metadata } from "next"
import Content from "@/components/evaluations/content"
import Layout from "@/components/cmsfullform/layout"

export const metadata: Metadata = {
  title: "Evaluations - LLM Quality Observer",
  description: "View LLM evaluation results and quality scores",
}

export default function EvaluationsPage() {
  return (
    <Layout>
      <Content />
    </Layout>
  )
}
