import { InfoPageLayout } from "@/components/InfoPageLayout"

export default function AboutPage() {
  return (
    <InfoPageLayout title="About InsightAI">
      <p>InsightAI is an AI-powered data analytics platform that helps you turn your data into insights effortlessly.</p>
      <section className="mt-8 space-y-4">
        <h2 className="text-2xl font-semibold text-charcoal">Our Mission</h2>
        <p>Our mission is to democratize data analytics through agentic automation and natural language understanding.</p>
        <h2 className="text-2xl font-semibold text-charcoal">Our Team</h2>
        <p>We are a team of data scientists, software engineers, and AI researchers dedicated to making data analytics accessible to everyone.</p>
      </section>
    </InfoPageLayout>
  )
}
