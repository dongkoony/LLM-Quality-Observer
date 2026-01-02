import type { Metadata } from "next"
import Content from "@/components/logs/content"
import Layout from "@/components/cmsfullform/layout"

export const metadata: Metadata = {
  title: "Logs - LLM Quality Observer",
  description: "View and search LLM request/response logs",
}

export default function LogsPage() {
  return (
    <Layout>
      <Content />
    </Layout>
  )
}
