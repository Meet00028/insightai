import { InfoPageLayout } from "@/components/InfoPageLayout"

export default function ContactPage() {
  return (
    <InfoPageLayout title="Contact Us">
      <p>Have questions or need support? Our team is here to help you with anything you need.</p>
      <section className="mt-8 space-y-4">
        <h2 className="text-2xl font-semibold text-charcoal">Get in Touch</h2>
        <div className="space-y-4">
          <div>
            <h3 className="text-lg font-semibold text-charcoal">Support</h3>
            <p>Email: support@insightai.com</p>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-charcoal">Sales</h3>
            <p>Email: sales@insightai.com</p>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-charcoal">General Inquiries</h3>
            <p>Email: hello@insightai.com</p>
          </div>
        </div>
      </section>
    </InfoPageLayout>
  )
}
