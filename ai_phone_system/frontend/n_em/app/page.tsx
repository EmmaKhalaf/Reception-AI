export default function Dashboard() {
  return (
    <div className="min-h-screen bg-gray-100 p-8">
      {/* Header */}
      <header className="flex justify-between items-center mb-10">
        <h1 className="text-3xl font-bold text-gray-800">Dashboard</h1>
        <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
          New Action
        </button>
      </header>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
        <div className="bg-white p-6 rounded-xl shadow">
          <h2 className="text-gray-500 text-sm">Total Calls</h2>
          <p className="text-3xl font-bold mt-2">128</p>
        </div>

        <div className="bg-white p-6 rounded-xl shadow">
          <h2 className="text-gray-500 text-sm">AI Responses</h2>
          <p className="text-3xl font-bold mt-2">94</p>
        </div>

        <div className="bg-white p-6 rounded-xl shadow">
          <h2 className="text-gray-500 text-sm">Success Rate</h2>
          <p className="text-3xl font-bold mt-2">87%</p>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white p-6 rounded-xl shadow">
        <h2 className="text-xl font-semibold mb-4">Recent Activity</h2>

        <ul className="space-y-4">
          <li className="flex justify-between border-b pb-3">
            <span>📞 Call from +1 514‑xxx‑xxxx</span>
            <span className="text-gray-500 text-sm">2 min ago</span>
          </li>

          <li className="flex justify-between border-b pb-3">
            <span>🤖 AI responded successfully</span>
            <span className="text-gray-500 text-sm">10 min ago</span>
          </li>

          <li className="flex justify-between">
            <span>⚠️ Missed call</span>
            <span className="text-gray-500 text-sm">1 hour ago</span>
          </li>
        </ul>
      </div>
    </div>
  );
}