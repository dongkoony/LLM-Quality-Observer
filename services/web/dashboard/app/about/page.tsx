import type { Metadata } from "next"
import Content from "@/components/about/content"
import Layout from "@/components/cmsfullform/layout"

export const metadata: Metadata = {
  title: "About - LLM Quality Observer",
  description: "Learn about the LLM Quality Observer platform",
}

export default function AboutPage() {
  return (
    <Layout>
      <Content />
    </Layout>
  )
}
