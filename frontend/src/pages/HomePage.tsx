import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Search, DollarSign, BarChart3, Smartphone, Bell, Bot } from 'lucide-react';

const HomePage: React.FC = () => {
  const features = [
    {
      icon: Search,
      title: 'Advanced Search',
      description: 'Lightning-fast search across 50,000+ Pokemon cards with intelligent filters and sorting.',
    },
    {
      icon: DollarSign,
      title: 'Real-Time Pricing',
      description: 'Live pricing data from TCGPlayer and eBay with ML-powered trend analysis.',
    },
    {
      icon: BarChart3,
      title: 'Market Intelligence',
      description: 'Professional-grade analytics and insights for informed investment decisions.',
    },
    {
      icon: Smartphone,
      title: 'Portfolio Management',
      description: 'Track your collection value with automated price updates and performance metrics.',
    },
    {
      icon: Bell,
      title: 'Smart Alerts',
      description: 'Get notified of price changes, new listings, and market opportunities.',
    },
    {
      icon: Bot,
      title: 'AI-Powered',
      description: 'Machine learning algorithms for price predictions and investment recommendations.',
    },
  ];

  const pricingTiers = [
    {
      name: 'Free',
      price: '$0',
      description: 'Perfect for casual collectors',
      features: [
        'Basic card search',
        'Current market prices',
        '100 API calls/hour',
        'Community support',
      ],
      cta: 'Get Started',
      popular: false,
    },
    {
      name: 'Gold',
      price: '$19',
      description: 'For serious collectors and traders',
      features: [
        'Advanced search & filters',
        'Historical price data',
        'Portfolio management',
        'Price alerts',
        '1,000 API calls/hour',
        'Email support',
      ],
      cta: 'Start Free Trial',
      popular: true,
    },
    {
      name: 'Platinum',
      price: '$49',
      description: 'For professional investors',
      features: [
        'Full market intelligence',
        'Real-time data streaming',
        'Advanced analytics',
        'Custom alerts & webhooks',
        '10,000 API calls/hour',
        'Priority support',
        'API access',
      ],
      cta: 'Contact Sales',
      popular: false,
    },
  ];

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative bg-gradient-to-br from-poke-blue via-blue-600 to-poke-red overflow-hidden">
        <div className="absolute inset-0 bg-black opacity-10"></div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
          <div className="text-center">
            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8 }}
              className="text-4xl md:text-6xl font-bold text-white mb-6"
            >
              Professional Pokemon TCG
              <br />
              <span className="text-poke-yellow">Market Intelligence</span>
            </motion.h1>
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.2 }}
              className="text-xl text-blue-100 mb-8 max-w-3xl mx-auto"
            >
              Get real-time pricing, advanced analytics, and market insights for your Pokemon card 
              collection. Join thousands of collectors and investors using our platform.
            </motion.p>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.4 }}
              className="flex flex-col sm:flex-row gap-4 justify-center"
            >
              <Link
                to="/search"
                className="bg-poke-yellow text-poke-blue px-8 py-4 rounded-lg font-semibold text-lg hover:bg-yellow-400 transition-colors"
              >
                Start Searching Cards
              </Link>
              <Link
                to="/pricing"
                className="bg-white bg-opacity-20 text-white px-8 py-4 rounded-lg font-semibold text-lg hover:bg-opacity-30 transition-colors backdrop-blur-sm"
              >
                View Pricing Plans
              </Link>
            </motion.div>
          </div>
        </div>

        {/* Floating Cards Animation */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          {[...Array(6)].map((_, i) => (
            <motion.div
              key={i}
              className="absolute w-16 h-24 bg-gradient-to-br from-yellow-400 to-yellow-600 rounded-lg shadow-lg opacity-20"
              style={{
                left: `${10 + i * 15}%`,
                top: `${20 + (i % 3) * 20}%`,
              }}
              animate={{
                y: [0, -20, 0],
                rotate: [0, 5, -5, 0],
              }}
              transition={{
                duration: 4 + i,
                repeat: Infinity,
                ease: "easeInOut",
              }}
            />
          ))}
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Everything You Need for Pokemon TCG Success
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              From casual collecting to professional investing, our platform provides 
              the tools and insights you need to make informed decisions.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
                className="text-center p-6 rounded-xl hover:shadow-lg transition-shadow"
              >
                <div className="flex justify-center mb-4">
                  <feature.icon size={40} className="text-poke-blue" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  {feature.title}
                </h3>
                <p className="text-gray-600">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section className="py-24 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Choose Your Plan
            </h2>
            <p className="text-xl text-gray-600">
              Start free and upgrade as your collection grows
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {pricingTiers.map((tier, index) => (
              <motion.div
                key={tier.name}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
                className={`relative rounded-2xl p-8 ${
                  tier.popular
                    ? 'bg-poke-blue text-white ring-4 ring-blue-200'
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

                <div className="text-center">
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

                <ul className="mt-8 space-y-3">
                  {tier.features.map((feature) => (
                    <li key={feature} className="flex items-center">
                      <span className={`mr-3 ${tier.popular ? 'text-poke-yellow' : 'text-green-500'}`}>
                        ✓
                      </span>
                      <span className={tier.popular ? 'text-blue-100' : 'text-gray-600'}>
                        {feature}
                      </span>
                    </li>
                  ))}
                </ul>

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

      {/* CTA Section */}
      <section className="py-24 bg-poke-blue">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Ready to Level Up Your Pokemon TCG Game?
          </h2>
          <p className="text-xl text-blue-100 mb-8 max-w-2xl mx-auto">
            Join thousands of collectors and investors who trust our platform 
            for their Pokemon TCG market intelligence needs.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to="/search"
              className="bg-poke-yellow text-poke-blue px-8 py-4 rounded-lg font-semibold text-lg hover:bg-yellow-400 transition-colors"
            >
              Start Free Today
            </Link>
            <a
              href="/api/docs"
              className="bg-white bg-opacity-20 text-white px-8 py-4 rounded-lg font-semibold text-lg hover:bg-opacity-30 transition-colors backdrop-blur-sm"
            >
              Explore API
            </a>
          </div>
        </div>
      </section>
    </div>
  );
};

export default HomePage;