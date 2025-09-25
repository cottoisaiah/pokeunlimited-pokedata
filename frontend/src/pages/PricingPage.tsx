import React from 'react';
import { motion } from 'framer-motion';

const PricingPage: React.FC = () => {
  const pricingTiers = [
    {
      name: 'Free',
      price: '$0',
      description: 'Perfect for casual collectors',
      features: [
        'Basic card search and browsing',
        'Current market prices',
        'Community forums access',
        '100 API calls per hour',
        'Email support',
      ],
      limitations: [
        'No historical price data',
        'Limited search filters',
        'No portfolio management',
        'No price alerts',
      ],
      cta: 'Get Started Free',
      popular: false,
      color: 'gray',
    },
    {
      name: 'Gold',
      price: '$19',
      description: 'For serious collectors and traders',
      features: [
        'Everything in Free, plus:',
        'Advanced search with all filters',
        'Historical price data (6 months)',
        'Portfolio management and tracking',
        'Price alerts and notifications',
        'Market trend analysis',
        '1,000 API calls per hour',
        'Priority email support',
        'Export data to CSV',
      ],
      limitations: [
        'Limited to 6 months historical data',
        'Basic analytics only',
      ],
      cta: 'Start 14-Day Free Trial',
      popular: true,
      color: 'blue',
    },
    {
      name: 'Platinum',
      price: '$49',
      description: 'For professional investors and businesses',
      features: [
        'Everything in Gold, plus:',
        'Full historical price data (5+ years)',
        'Advanced analytics and insights',
        'Real-time price streaming',
        'Custom alerts and webhooks',
        'Bulk data exports',
        'API access with documentation',
        '10,000 API calls per hour',
        'Phone and priority support',
        'White-label options available',
      ],
      limitations: [],
      cta: 'Contact Sales',
      popular: false,
      color: 'purple',
    },
  ];

  const faqs = [
    {
      question: 'What payment methods do you accept?',
      answer: 'We accept all major credit cards (Visa, Mastercard, American Express), PayPal, and bank transfers for enterprise accounts.',
    },
    {
      question: 'Can I change my plan anytime?',
      answer: 'Yes, you can upgrade or downgrade your plan at any time. Changes take effect immediately, and we\'ll prorate any charges.',
    },
    {
      question: 'Is there a free trial?',
      answer: 'Yes! We offer a 14-day free trial for both Gold and Platinum plans. No credit card required to start.',
    },
    {
      question: 'What is included in API access?',
      answer: 'API access includes real-time pricing data, historical data, search endpoints, and comprehensive documentation. Rate limits vary by plan.',
    },
    {
      question: 'Do you offer discounts for annual billing?',
      answer: 'Yes, we offer 2 months free when you pay annually. That\'s a 17% discount on all paid plans.',
    },
    {
      question: 'Can I cancel anytime?',
      answer: 'Absolutely. You can cancel your subscription at any time with no cancellation fees. Your access continues until the end of your billing period.',
    },
  ];

  const apiFeatures = [
    {
      icon: '🔍',
      title: 'Search API',
      description: 'Search through our entire database of Pokemon cards with advanced filtering options.',
    },
    {
      icon: '💰',
      title: 'Pricing API',
      description: 'Get real-time and historical pricing data for any card with market analytics.',
    },
    {
      icon: '📊',
      title: 'Analytics API',
      description: 'Access market trends, volatility data, and investment insights.',
    },
    {
      icon: '🔔',
      title: 'Webhooks',
      description: 'Receive real-time notifications for price changes and market events.',
    },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-poke-blue to-blue-700 py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="text-4xl md:text-5xl font-bold text-white mb-6"
          >
            Choose Your Plan
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="text-xl text-blue-100 mb-8 max-w-3xl mx-auto"
          >
            From casual collecting to professional investing, we have the perfect plan 
            to help you succeed in the Pokemon TCG market.
          </motion.p>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
            className="bg-white bg-opacity-20 backdrop-blur-sm rounded-lg p-4 inline-block"
          >
            <p className="text-white font-medium">
              💎 All paid plans include a 14-day free trial
            </p>
          </motion.div>
        </div>
      </section>

      {/* Pricing Tiers */}
      <section className="py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {pricingTiers.map((tier, index) => (
              <motion.div
                key={tier.name}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className={`relative rounded-2xl p-8 ${
                  tier.popular
                    ? 'bg-poke-blue text-white ring-4 ring-blue-200 scale-105'
                    : 'bg-white border border-gray-200'
                }`}
              >
                {tier.popular && (
                  <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                    <span className="bg-poke-yellow text-poke-blue px-4 py-1 rounded-full text-sm font-semibold">
                      Most Popular
                    </span>
                  </div>
                )}

                <div className="text-center mb-8">
                  <h3 className={`text-2xl font-bold ${tier.popular ? 'text-white' : 'text-gray-900'}`}>
                    {tier.name}
                  </h3>
                  <div className="mt-4">
                    <span className={`text-4xl font-bold ${tier.popular ? 'text-white' : 'text-gray-900'}`}>
                      {tier.price}
                    </span>
                    {tier.price !== '$0' && (
                      <span className={`text-lg ${tier.popular ? 'text-blue-100' : 'text-gray-500'}`}>
                        /month
                      </span>
                    )}
                  </div>
                  <p className={`mt-2 ${tier.popular ? 'text-blue-100' : 'text-gray-600'}`}>
                    {tier.description}
                  </p>
                </div>

                <div className="space-y-6">
                  {/* Features */}
                  <div>
                    <h4 className={`font-semibold mb-3 ${tier.popular ? 'text-white' : 'text-gray-900'}`}>
                      ✅ Included Features
                    </h4>
                    <ul className="space-y-2">
                      {tier.features.map((feature) => (
                        <li key={feature} className="flex items-start">
                          <span className={`mr-3 mt-0.5 ${tier.popular ? 'text-poke-yellow' : 'text-green-500'}`}>
                            ✓
                          </span>
                          <span className={`text-sm ${tier.popular ? 'text-blue-100' : 'text-gray-600'}`}>
                            {feature}
                          </span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Limitations */}
                  {tier.limitations.length > 0 && (
                    <div>
                      <h4 className={`font-semibold mb-3 ${tier.popular ? 'text-blue-100' : 'text-gray-700'}`}>
                        ⚠️ Limitations
                      </h4>
                      <ul className="space-y-2">
                        {tier.limitations.map((limitation) => (
                          <li key={limitation} className="flex items-start">
                            <span className={`mr-3 mt-0.5 ${tier.popular ? 'text-blue-300' : 'text-orange-500'}`}>
                              ⊘
                            </span>
                            <span className={`text-sm ${tier.popular ? 'text-blue-200' : 'text-gray-500'}`}>
                              {limitation}
                            </span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                <button
                  className={`w-full mt-8 px-6 py-3 rounded-lg font-semibold transition-colors ${
                    tier.popular
                      ? 'bg-poke-yellow text-poke-blue hover:bg-yellow-400'
                      : 'bg-poke-blue text-white hover:bg-blue-700'
                  }`}
                >
                  {tier.cta}
                </button>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* API Features */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Powerful API for Developers
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Build amazing applications with our comprehensive Pokemon TCG data API. 
              Trusted by developers and businesses worldwide.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {apiFeatures.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
                className="text-center p-6"
              >
                <div className="text-4xl mb-4">{feature.icon}</div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {feature.title}
                </h3>
                <p className="text-gray-600 text-sm">{feature.description}</p>
              </motion.div>
            ))}
          </div>

          <div className="text-center mt-12">
            <a
              href="/api/docs"
              className="bg-poke-blue text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors inline-block"
            >
              View API Documentation
            </a>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Frequently Asked Questions
            </h2>
            <p className="text-xl text-gray-600">
              Everything you need to know about our pricing and plans
            </p>
          </div>

          <div className="space-y-6">
            {faqs.map((faq, index) => (
              <motion.div
                key={faq.question}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
                className="bg-white rounded-lg p-6 shadow-sm"
              >
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {faq.question}
                </h3>
                <p className="text-gray-600">{faq.answer}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 bg-poke-blue">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to Get Started?
          </h2>
          <p className="text-xl text-blue-100 mb-8">
            Join thousands of Pokemon TCG collectors and investors using our platform
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button className="bg-poke-yellow text-poke-blue px-8 py-4 rounded-lg font-semibold text-lg hover:bg-yellow-400 transition-colors">
              Start Free Trial
            </button>
            <button className="bg-white bg-opacity-20 text-white px-8 py-4 rounded-lg font-semibold text-lg hover:bg-opacity-30 transition-colors backdrop-blur-sm">
              Contact Sales
            </button>
          </div>
        </div>
      </section>
    </div>
  );
};

export default PricingPage;