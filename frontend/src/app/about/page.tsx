export default function About() {
  return (
    <div className="max-w-3xl mx-auto py-12 px-6">
      <h1 className="text-3xl font-medium mb-8">About NiftyFlow</h1>
      
      <div className="space-y-6 text-[var(--gf-gray-text)] leading-relaxed">
        <section>
          <h2 className="text-xl font-medium text-[var(--foreground)] mb-3">Our Mission</h2>
          <p>
            NiftyFlow is designed to empower retail investors in the Indian stock market with 
            institutional-grade portfolio tracking and machine-learning-driven insights, wrapped 
            in a clean, distraction-free interface.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-medium text-[var(--foreground)] mb-3">Technology Stack</h2>
          <p>
            Built for scale and security, NiftyFlow utilizes a modern stack:
          </p>
          <ul className="list-disc pl-5 mt-2 space-y-1">
            <li><strong>Frontend:</strong> Next.js 14, React, Tailwind CSS</li>
            <li><strong>Backend:</strong> FastAPI, Python, SQLAlchemy</li>
            <li><strong>Database:</strong> PostgreSQL with Row-Level Security (RLS)</li>
            <li><strong>Background Jobs:</strong> Celery, Redis</li>
            <li><strong>Market Data:</strong> yfinance API</li>
          </ul>
        </section>
        
        <section>
          <h2 className="text-xl font-medium text-[var(--foreground)] mb-3">Machine Learning</h2>
          <p>
            Our predictive insights are powered by an XGBoost model running asynchronously on 
            a distributed task queue. It evaluates historical market data to generate probabilistic 
            momentum indicators, providing a quick summary of market sentiment.
          </p>
        </section>
      </div>
    </div>
  );
}
