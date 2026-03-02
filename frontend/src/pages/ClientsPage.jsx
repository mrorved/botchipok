import { useEffect, useState } from 'react'
import api from '../api/client'
import { ChevronDown } from 'lucide-react'

const STATUS_LABELS = {
  pending: 'На подтверждении', confirmed: 'Подтверждён', adjusted: 'С корректировкой',
  paid: 'Оплачен', issued: 'Выдан',
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
              <div className="w-9 h-9 bg-ink-800 rounded-xl flex items-center justify-center text-sm font-semibold text-amber-400">
                {(client.full_name || client.username || '?')[0].toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium">{client.full_name || client.username || `ID ${client.telegram_id}`}</p>
                <p className="text-xs text-ink-500 mt-0.5">
                  {client.username ? `@${client.username}` : ''} · tg_id: {client.telegram_id}
                </p>
              </div>
              <p className="text-xs text-ink-500">{new Date(client.created_at).toLocaleDateString('ru')}</p>
              <ChevronDown size={14} className={`text-ink-500 transition-transform ${expanded === client.id ? 'rotate-180' : ''}`} />
            </div>

            {expanded === client.id && orders[client.id] && (
              <div className="border-t border-ink-800 p-4">
                <div className="flex justify-between items-center mb-3">
                  <p className="text-xs text-ink-500 font-medium uppercase tracking-wide">История заказов</p>
                  <p className="text-sm font-mono text-amber-400">
                    Итого: {orders[client.id].total_amount?.toFixed(0)} ₽
                  </p>
                </div>
                {orders[client.id].orders?.length === 0 && (
                  <p className="text-sm text-ink-600">Заказов нет</p>
                )}
                <div className="space-y-1.5">
                  {orders[client.id].orders?.map(o => (
                    <div key={o.id} className="flex items-center justify-between bg-ink-800 rounded-lg px-3 py-2 text-sm">
                      <span className="font-mono text-amber-500">#{o.id}</span>
                      <span className="text-ink-400">{new Date(o.created_at).toLocaleDateString('ru')}</span>
                      <span className="text-ink-300">{STATUS_LABELS[o.status]}</span>
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
