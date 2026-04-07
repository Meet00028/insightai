import { InfoPageLayout } from "@/components/InfoPageLayout"

export default function BlogPage() {
  return (
    <InfoPageLayout title="Blog & Insights">
      <p>Stay up-to-date with the latest trends and insights in data analytics and AI.</p>
      <section className="mt-8 space-y-4">
        <h2 className="text-2xl font-semibold text-charcoal">Latest Posts</h2>
        <div className="space-y-8">
          <div className="border-b border-beige pb-6">
            <h3 className="text-xl font-semibold text-charcoal">The Future of AI-Powered Data Analytics</h3>
            <p className="text-sm text-warm-gray mt-2">February 24, 2024 • 5 min read</p>
            <p className="mt-4">How agentic automation is revolutionizing the way we analyze data.</p>
          </div>
          <div className="border-b border-beige pb-6">
            <h3 className="text-xl font-semibold text-charcoal">Natural Language Data Querying: A New Paradigm</h3>
            <p className="text-sm text-warm-gray mt-2">February 15, 2024 • 4 min read</p>
            <p className="mt-4">The rise of natural language processing for database querying.</p>
          </div>
        </div>
      </section>
    </InfoPageLayout>
  )
}
