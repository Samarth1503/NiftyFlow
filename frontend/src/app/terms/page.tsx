export default function Terms() {
  return (
    <div className="max-w-3xl mx-auto py-12 px-6">
      <h1 className="text-3xl font-medium mb-8">Terms of Service & Disclaimer</h1>
      
      <div className="space-y-6 text-[var(--gf-gray-text)] leading-relaxed">
        <section>
          <h2 className="text-xl font-medium text-[var(--foreground)] mb-3">1. Not Financial Advice</h2>
          <p>
            The information provided on NiftyFlow, including but not limited to price predictions, 
            market news, portfolio analytics, and machine learning insights, is for informational 
            and educational purposes only. It does not constitute financial, investment, legal, 
            or tax advice. You should consult a qualified financial advisor before making any 
            investment decisions.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-medium text-[var(--foreground)] mb-3">2. Accuracy of Data</h2>
          <p>
            While we strive to provide accurate and up-to-date information, NiftyFlow relies on 
            third-party data providers (e.g., Yahoo Finance). We do not guarantee the accuracy, 
            completeness, or timeliness of any market data or predictions. The XGBoost predictions 
            are probabilistic models and should not be used as the sole basis for any trade.
          </p>
        </section>
        
        <section>
          <h2 className="text-xl font-medium text-[var(--foreground)] mb-3">3. User Responsibilities</h2>
          <p>
            You are entirely responsible for the trades and investment decisions you make. 
            NiftyFlow and its creators accept no liability for any financial losses or damages 
            incurred from using this application.
          </p>
        </section>
      </div>
    </div>
  );
}
