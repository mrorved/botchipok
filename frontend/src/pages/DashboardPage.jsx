import { useEffect, useState } from 'react'
import api from '../api/client'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { ShoppingCart, Users, TrendingUp } from 'lucide-react'

const periods = [
  { key: 'day', label: 'День' },
  { key: 'week', label: 'Неделя' },
  { key: 'month', label: 'Месяц' },
]

export default function DashboardPage() {
  const [data, setData] = useState(null)
  const [period, setPeriod] = useState('week')

  useEffect(() => {
    api.get(`/api/analytics/?period=${period}`).then(r => setData(r.data))
  }, [period])

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold">Аналитика</h1>
        <div className="flex gap-1 bg-ink-900 border border-ink-800 rounded-xl p-1">
          {periods.map(p => (
            <button
              key={p.key}
              onClick={() => setPeriod(p.key)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                period === p.key
                  ? 'bg-amber-500 text-ink-950'
                  : 'text-ink-400 hover:text-ink-200'
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {data && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <StatCard
              icon={<ShoppingCart size={18} />}
              label="Заказов"
              value={data.orders_count}
              color="amber"
            />
            <StatCard
              icon={<Users size={18} />}
              label="Новых клиентов"
              value={data.new_users}
              color="blue"
            />
            <StatCard
              icon={<TrendingUp size={18} />}
              label="Топ-товаров"
              value={data.top_products.length}
              color="green"
            />
          </div>

          {data.top_products.length > 0 && (
            <div className="card p-5">
              <h2 className="text-sm font-semibold text-ink-300 mb-4">Топ товары по количеству</h2>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={data.top_products} layout="vertical">
                  <XAxis type="number" tick={{ fill: '#6b6b52', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis dataKey="name" type="category" width={150} tick={{ fill: '#b0b09a', fontSize: 12 }} axisLine={false} tickLine={false} />
                  <Tooltip
                    contentStyle={{ background: '#282821', border: '1px solid #3d3d30', borderRadius: 8 }}
                    labelStyle={{ color: '#e8e8e0' }}
                    itemStyle={{ color: '#fbbf24' }}
                  />
                  <Bar dataKey="quantity" radius={[0, 6, 6, 0]}>
                    {data.top_products.map((_, i) => (
                      <Cell key={i} fill={i === 0 ? '#f59e0b' : '#3d3d30'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </>
      )}
    </div>
  )
}

function StatCard({ icon, label, value, color }) {
  const colors = {
    amber: 'bg-amber-500/10 text-amber-400',
    blue: 'bg-blue-500/10 text-blue-400',
    green: 'bg-emerald-500/10 text-emerald-400',
  }
  return (
    <div className="card p-5 flex items-center gap-4">
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${colors[color]}`}>
        {icon}
      </div>
      <div>
        <p className="text-2xl font-semibold font-mono">{value}</p>
        <p className="text-xs text-ink-500 mt-0.5">{label}</p>
      </div>
    </div>
  )
}
