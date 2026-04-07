import { InfoPageLayout } from "@/components/InfoPageLayout"

export default function TermsPage() {
  return (
    <InfoPageLayout title="Terms of Service">
      <p>By using InsightAI, you agree to these terms. Please read them carefully.</p>
      <section className="mt-8 space-y-4">
        <h2 className="text-2xl font-semibold text-charcoal">1. Use of Service</h2>
        <p>You may use InsightAI only for lawful purposes and in accordance with these terms.</p>
        <h2 className="text-2xl font-semibold text-charcoal">2. User Responsibilities</h2>
        <p>You are responsible for the data you upload and the actions taken through your account.</p>
        <h2 className="text-2xl font-semibold text-charcoal">3. Intellectual Property</h2>
        <p>All content and technology on the InsightAI platform are the property of InsightAI or its licensors.</p>
      </section>
    </InfoPageLayout>
  )
}
