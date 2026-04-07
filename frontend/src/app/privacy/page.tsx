import { InfoPageLayout } from "@/components/InfoPageLayout"

export default function PrivacyPage() {
  return (
    <InfoPageLayout title="Privacy Policy">
      <p>At InsightAI, we take your privacy seriously. This policy describes how we collect, use, and protect your data.</p>
      <section className="mt-8 space-y-4">
        <h2 className="text-2xl font-semibold text-charcoal">1. Data Collection</h2>
        <p>We collect only the data necessary to provide our services, including account information and the data you upload for analysis.</p>
        <h2 className="text-2xl font-semibold text-charcoal">2. Data Security</h2>
        <p>Your data is encrypted at rest and in transit. We use industry-standard security measures to protect your information.</p>
        <h2 className="text-2xl font-semibold text-charcoal">3. Third-Party Sharing</h2>
        <p>We do not sell your personal data. We only share data with service providers who help us operate our platform.</p>
      </section>
    </InfoPageLayout>
  )
}
