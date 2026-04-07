import { InfoPageLayout } from "@/components/InfoPageLayout"

export default function SecurityPage() {
  return (
    <InfoPageLayout title="Security Overview">
      <p>Security is at the heart of InsightAI. We build our platform with multiple layers of protection.</p>
      <section className="mt-8 space-y-4">
        <h2 className="text-2xl font-semibold text-charcoal">1. Infrastructure Security</h2>
        <p>Our infrastructure is hosted on secure cloud providers with multi-factor authentication and strict access controls.</p>
        <h2 className="text-2xl font-semibold text-charcoal">2. Data Protection</h2>
        <p>All user data is encrypted with AES-256 at rest and TLS 1.2+ in transit.</p>
        <h2 className="text-2xl font-semibold text-charcoal">3. Compliance</h2>
        <p>We adhere to industry-standard compliance frameworks to ensure the highest level of security.</p>
      </section>
    </InfoPageLayout>
  )
}
