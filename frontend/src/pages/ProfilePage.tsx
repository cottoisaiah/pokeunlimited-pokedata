import React, { useState } from 'react';
import { motion } from 'framer-motion';

const ProfilePage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('profile');

  // Mock user data
  const user = {
    name: 'Alex Chen',
    email: 'alex.chen@example.com',
    plan: 'Gold',
    memberSince: '2023-06-15',
    avatar: 'https://via.placeholder.com/150x150/3742fa/ffffff?text=AC',
    totalCards: 247,
    totalValue: 15420.75,
    alertsEnabled: true,
    newsletterEnabled: true,
  };

  const apiKeys = [
    {
      id: 1,
      name: 'Production API Key',
      key: 'pk_live_abc123...',
      created: '2024-01-01',
      lastUsed: '2024-01-15',
      status: 'active',
    },
    {
      id: 2,
      name: 'Development API Key',
      key: 'pk_test_xyz789...',
      created: '2023-12-15',
      lastUsed: '2024-01-10',
      status: 'active',
    },
  ];

  const billingHistory = [
    {
      id: 1,
      date: '2024-01-01',
      amount: 19.00,
      status: 'paid',
      plan: 'Gold Monthly',
    },
    {
      id: 2,
      date: '2023-12-01',
      amount: 19.00,
      status: 'paid',
      plan: 'Gold Monthly',
    },
    {
      id: 3,
      date: '2023-11-01',
      amount: 19.00,
      status: 'paid',
      plan: 'Gold Monthly',
    },
  ];

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const tabs = [
    { id: 'profile', name: 'Profile', icon: '👤' },
    { id: 'subscription', name: 'Subscription', icon: '💳' },
    { id: 'api', name: 'API Keys', icon: '🔑' },
    { id: 'notifications', name: 'Notifications', icon: '🔔' },
  ];

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Page Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Account Settings
          </h1>
          <p className="text-gray-600">
            Manage your profile, subscription, and preferences
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Sidebar Navigation */}
          <div className="lg:col-span-1">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5 }}
              className="bg-white rounded-lg shadow-sm p-6"
            >
              <div className="text-center mb-6">
                <img
                  src={user.avatar}
                  alt={user.name}
                  className="w-20 h-20 rounded-full mx-auto mb-3"
                />
                <h3 className="font-semibold text-gray-900">{user.name}</h3>
                <p className="text-sm text-gray-600">{user.plan} Plan</p>
              </div>

              <nav className="space-y-2">
                {tabs.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left transition-colors ${
                      activeTab === tab.id
                        ? 'bg-poke-blue text-white'
                        : 'text-gray-600 hover:bg-gray-100'
                    }`}
                  >
                    <span>{tab.icon}</span>
                    <span>{tab.name}</span>
                  </button>
                ))}
              </nav>
            </motion.div>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
              className="bg-white rounded-lg shadow-sm p-6"
            >
              {/* Profile Tab */}
              {activeTab === 'profile' && (
                <div>
                  <h2 className="text-xl font-semibold text-gray-900 mb-6">
                    Profile Information
                  </h2>
                  
                  <form className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Full Name
                        </label>
                        <input
                          type="text"
                          defaultValue={user.name}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-poke-blue"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Email Address
                        </label>
                        <input
                          type="email"
                          defaultValue={user.email}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-poke-blue"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Password
                      </label>
                      <button className="text-poke-blue font-medium hover:text-blue-700">
                        Change Password
                      </button>
                    </div>

                    <div className="pt-4 border-t border-gray-200">
                      <h3 className="text-lg font-medium text-gray-900 mb-4">
                        Account Statistics
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="text-center p-4 bg-gray-50 rounded-lg">
                          <div className="text-2xl font-bold text-poke-blue">
                            {user.totalCards}
                          </div>
                          <div className="text-sm text-gray-600">Total Cards</div>
                        </div>
                        <div className="text-center p-4 bg-gray-50 rounded-lg">
                          <div className="text-2xl font-bold text-poke-blue">
                            {formatCurrency(user.totalValue)}
                          </div>
                          <div className="text-sm text-gray-600">Portfolio Value</div>
                        </div>
                        <div className="text-center p-4 bg-gray-50 rounded-lg">
                          <div className="text-2xl font-bold text-poke-blue">
                            {formatDate(user.memberSince)}
                          </div>
                          <div className="text-sm text-gray-600">Member Since</div>
                        </div>
                      </div>
                    </div>

                    <button className="bg-poke-blue text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors">
                      Save Changes
                    </button>
                  </form>
                </div>
              )}

              {/* Subscription Tab */}
              {activeTab === 'subscription' && (
                <div>
                  <h2 className="text-xl font-semibold text-gray-900 mb-6">
                    Subscription & Billing
                  </h2>

                  {/* Current Plan */}
                  <div className="bg-gradient-to-r from-poke-blue to-blue-600 rounded-lg p-6 text-white mb-8">
                    <h3 className="text-lg font-semibold mb-2">Current Plan</h3>
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-2xl font-bold">{user.plan} Plan</div>
                        <div className="text-blue-100">$19/month • Billed monthly</div>
                      </div>
                      <button className="bg-white text-poke-blue px-4 py-2 rounded-lg font-medium hover:bg-gray-100 transition-colors">
                        Change Plan
                      </button>
                    </div>
                  </div>

                  {/* Usage Stats */}
                  <div className="mb-8">
                    <h3 className="text-lg font-medium text-gray-900 mb-4">
                      Current Usage
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="border border-gray-200 rounded-lg p-4">
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-sm text-gray-600">API Calls</span>
                          <span className="text-sm font-medium">2,847 / 10,000</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div className="bg-poke-blue h-2 rounded-full" style={{width: '28.47%'}}></div>
                        </div>
                      </div>
                      <div className="border border-gray-200 rounded-lg p-4">
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-sm text-gray-600">Price Alerts</span>
                          <span className="text-sm font-medium">12 / 50</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div className="bg-poke-yellow h-2 rounded-full" style={{width: '24%'}}></div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Billing History */}
                  <div>
                    <h3 className="text-lg font-medium text-gray-900 mb-4">
                      Billing History
                    </h3>
                    <div className="border border-gray-200 rounded-lg overflow-hidden">
                      <table className="w-full">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Date</th>
                            <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Plan</th>
                            <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Amount</th>
                            <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Status</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200">
                          {billingHistory.map((bill) => (
                            <tr key={bill.id}>
                              <td className="px-4 py-3 text-sm text-gray-900">
                                {formatDate(bill.date)}
                              </td>
                              <td className="px-4 py-3 text-sm text-gray-900">
                                {bill.plan}
                              </td>
                              <td className="px-4 py-3 text-sm text-gray-900">
                                {formatCurrency(bill.amount)}
                              </td>
                              <td className="px-4 py-3">
                                <span className="inline-flex px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">
                                  {bill.status}
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}

              {/* API Keys Tab */}
              {activeTab === 'api' && (
                <div>
                  <h2 className="text-xl font-semibold text-gray-900 mb-6">
                    API Keys
                  </h2>

                  <div className="mb-6">
                    <button className="bg-poke-blue text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors">
                      Create New API Key
                    </button>
                  </div>

                  <div className="space-y-4">
                    {apiKeys.map((key) => (
                      <div key={key.id} className="border border-gray-200 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <h3 className="font-medium text-gray-900">{key.name}</h3>
                          <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                            key.status === 'active' 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {key.status}
                          </span>
                        </div>
                        <div className="bg-gray-100 rounded-md p-3 mb-3">
                          <code className="text-sm text-gray-800">{key.key}</code>
                        </div>
                        <div className="flex items-center justify-between text-sm text-gray-600">
                          <div>
                            Created: {formatDate(key.created)} | 
                            Last used: {formatDate(key.lastUsed)}
                          </div>
                          <div className="space-x-2">
                            <button className="text-poke-blue hover:text-blue-700">
                              Copy
                            </button>
                            <button className="text-red-600 hover:text-red-700">
                              Revoke
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="mt-8 p-4 bg-blue-50 rounded-lg">
                    <h3 className="font-medium text-blue-900 mb-2">
                      🔒 Keep your API keys secure
                    </h3>
                    <p className="text-sm text-blue-700">
                      Never share your API keys in publicly accessible areas such as GitHub, 
                      client-side code, and so forth. Always use environment variables.
                    </p>
                  </div>
                </div>
              )}

              {/* Notifications Tab */}
              {activeTab === 'notifications' && (
                <div>
                  <h2 className="text-xl font-semibold text-gray-900 mb-6">
                    Notification Preferences
                  </h2>

                  <form className="space-y-6">
                    <div>
                      <h3 className="text-lg font-medium text-gray-900 mb-4">
                        Email Notifications
                      </h3>
                      <div className="space-y-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <div className="font-medium text-gray-900">Price Alerts</div>
                            <div className="text-sm text-gray-600">
                              Get notified when cards reach your target prices
                            </div>
                          </div>
                          <input
                            type="checkbox"
                            defaultChecked={user.alertsEnabled}
                            className="h-4 w-4 text-poke-blue focus:ring-poke-blue border-gray-300 rounded"
                          />
                        </div>
                        <div className="flex items-center justify-between">
                          <div>
                            <div className="font-medium text-gray-900">Market Updates</div>
                            <div className="text-sm text-gray-600">
                              Weekly market trends and insights
                            </div>
                          </div>
                          <input
                            type="checkbox"
                            defaultChecked={user.newsletterEnabled}
                            className="h-4 w-4 text-poke-blue focus:ring-poke-blue border-gray-300 rounded"
                          />
                        </div>
                        <div className="flex items-center justify-between">
                          <div>
                            <div className="font-medium text-gray-900">Portfolio Reports</div>
                            <div className="text-sm text-gray-600">
                              Monthly portfolio performance summaries
                            </div>
                          </div>
                          <input
                            type="checkbox"
                            defaultChecked={true}
                            className="h-4 w-4 text-poke-blue focus:ring-poke-blue border-gray-300 rounded"
                          />
                        </div>
                      </div>
                    </div>

                    <div>
                      <h3 className="text-lg font-medium text-gray-900 mb-4">
                        Push Notifications
                      </h3>
                      <div className="space-y-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <div className="font-medium text-gray-900">Instant Alerts</div>
                            <div className="text-sm text-gray-600">
                              Real-time price and volume alerts
                            </div>
                          </div>
                          <input
                            type="checkbox"
                            defaultChecked={true}
                            className="h-4 w-4 text-poke-blue focus:ring-poke-blue border-gray-300 rounded"
                          />
                        </div>
                      </div>
                    </div>

                    <button className="bg-poke-blue text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors">
                      Save Preferences
                    </button>
                  </form>
                </div>
              )}
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;