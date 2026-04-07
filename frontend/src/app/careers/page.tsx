import { InfoPageLayout } from "@/components/InfoPageLayout"

export default function CareersPage() {
  return (
    <InfoPageLayout title="Join Our Team">
      <p>We are always looking for talented individuals to join our team and help us build the future of data analytics.</p>
      <section className="mt-8 space-y-4">
        <h2 className="text-2xl font-semibold text-charcoal">Open Roles</h2>
        <div className="space-y-6">
          <div className="border border-beige rounded-2xl p-6 hover:border-charcoal transition-colors">
            <h3 className="text-xl font-semibold text-charcoal">AI Research Scientist</h3>
            <p className="text-sm text-warm-gray mt-2">Remote • Full-time</p>
            <p className="mt-4">Join our AI research team to develop state-of-the-art models for data analytics.</p>
          </div>
          <div className="border border-beige rounded-2xl p-6 hover:border-charcoal transition-colors">
            <h3 className="text-xl font-semibold text-charcoal">Senior Frontend Engineer</h3>
            <p className="text-sm text-warm-gray mt-2">San Francisco, CA • Full-time</p>
            <p className="mt-4">Help us build beautiful and intuitive user interfaces for our data platform.</p>
          </div>
        </div>
      </section>
    </InfoPageLayout>
  )
}
