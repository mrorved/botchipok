import { useEffect, useState } from 'react'
import api from '../api/client'
import { ChevronDown, Phone } from 'lucide-react'

const STATUS_LABELS = {
  pending: 'На подтверждении', confirmed: 'Подтверждён', adjusted: 'С корректировкой',
  paid: 'Оплачен', issued: 'Выдан',
}

const STATUS_COLORS = {
  pending:   'text-yellow-400',
  confirmed: 'text-blue-400',
  adjusted:  'text-purple-400',
  paid:      'text-emerald-400',
  issued:    'text-ink-400',
  cancelled: 'text-red-400',
}

export default function ClientsPage() {
  const [clients, setClients] = useState([])
  const [expanded, setExpanded] = useState(null)
  const [orders, setOrders] = useState({})

  useEffect(() => { api.get('/api/clients/').then(r => setClients(r.data)) }, [])

  const toggleClient = async (id) => {
    if (expanded === id) { setExpanded(null); return }
    setExpanded(id)
    if (!orders[id]) {
      const r = await api.get(`/api/clients/${id}/orders`)
      setOrders(o => ({ ...o, [id]: r.data }))
    }
  }

  return (
    <div>
      <h1 className="text-xl font-semibold mb-6">Клиенты</h1>

      <div className="space-y-2">
        {clients.length === 0 && (
          <div className="card p-10 text-center text-ink-500 text-sm">Клиентов нет</div>
        )}
        {clients.map(client => (
          <div key={client.id} className="card overflow-hidden">
            <div
              className="flex items-center gap-4 p-4 cursor-pointer hover:bg-ink-800/30 transition-colors"
              onClick={() => toggleClient(client.id)}
            >
              {/* Аватар */}
              <div className="w-9 h-9 bg-ink-800 rounded-xl flex items-center justify-center text-sm font-semibold text-amber-400 shrink-0">
                {(client.full_name || client.username || '?')[0].toUpperCase()}
              </div>

              {/* Основная инфо */}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-ink-100">
                  {client.full_name || client.username || `ID ${client.telegram_id}`}
                  {client.username && (
                    <span className="text-ink-500 font-normal ml-1.5">@{client.username}</span>
                  )}
                </p>
                <p className="text-xs text-ink-500 mt-0.5">
                  tg_id: {client.telegram_id}
                </p>
              </div>

              {/* Телефон */}
              {client.phone ? (
                <div className="flex items-center gap-1.5 text-xs text-amber-400/80 font-mono shrink-0">
                  <Phone size={11} />
                  {client.phone}
                </div>
              ) : (
                <div className="text-xs text-ink-700 shrink-0">нет телефона</div>
              )}

              {/* Дата регистрации */}
              <p className="text-xs text-ink-500 shrink-0 hidden sm:block">
                {new Date(client.created_at).toLocaleDateString('ru')}
              </p>

              <ChevronDown size={14} className={`text-ink-500 transition-transform shrink-0 ${expanded === client.id ? 'rotate-180' : ''}`} />
            </div>

            {expanded === client.id && orders[client.id] && (
              <div className="border-t border-ink-800 p-4">
                {/* Сводка */}
                <div className="flex flex-wrap gap-4 mb-4">
                  <div className="bg-ink-800/60 rounded-xl px-4 py-2.5 text-center">
                    <p className="text-lg font-mono font-semibold text-amber-400">
                      {orders[client.id].total_amount?.toFixed(0)} ₽
                    </p>
                    <p className="text-xs text-ink-500 mt-0.5">Всего потрачено</p>
                  </div>
                  <div className="bg-ink-800/60 rounded-xl px-4 py-2.5 text-center">
                    <p className="text-lg font-mono font-semibold text-ink-200">
                      {orders[client.id].orders?.length || 0}
                    </p>
                    <p className="text-xs text-ink-500 mt-0.5">Заказов</p>
                  </div>
                  {client.phone && (
                    <div className="bg-ink-800/60 rounded-xl px-4 py-2.5 flex items-center gap-2">
                      <Phone size={13} className="text-amber-400/70" />
                      <div>
                        <p className="text-sm font-mono text-amber-400">{client.phone}</p>
                        <p className="text-xs text-ink-500 mt-0.5">Телефон</p>
                      </div>
                    </div>
                  )}
                </div>

                {/* История заказов */}
                <p className="text-xs text-ink-500 font-medium uppercase tracking-wide mb-2">История заказов</p>
                {orders[client.id].orders?.length === 0 && (
                  <p className="text-sm text-ink-600">Заказов нет</p>
                )}
                <div className="space-y-1.5">
                  {orders[client.id].orders?.map(o => (
                    <div key={o.id} className="flex items-center justify-between bg-ink-800 rounded-lg px-3 py-2 text-sm">
                      <span className="font-mono text-amber-500 w-14">#{o.id}</span>
                      <span className="text-ink-400 flex-1 text-center">
                        {new Date(o.created_at).toLocaleDateString('ru')}
                      </span>
                      <span className={`${STATUS_COLORS[o.status] || 'text-ink-300'} text-xs`}>
                        {STATUS_LABELS[o.status] || o.status}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
