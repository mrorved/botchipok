import { useEffect, useState } from 'react'
import api from '../api/client'
import toast from 'react-hot-toast'
import { ChevronDown, Send } from 'lucide-react'

const STATUS_LABELS = {
  pending: 'На подтверждении', confirmed: 'Подтверждён', adjusted: 'С корректировкой',
  paid: 'Оплачен', issued: 'Выдан', cancelled: 'Отменён',
}

const STATUS_COLORS = {
  pending: 'text-yellow-400', confirmed: 'text-blue-400', adjusted: 'text-purple-400',
  paid: 'text-emerald-400', issued: 'text-ink-400', cancelled: 'text-red-400',
}

export default function ClientsPage() {
  const [clients, setClients] = useState([])
  const [expanded, setExpanded] = useState(null)
  const [orders, setOrders] = useState({})
  const [msgModal, setMsgModal] = useState(null)
  const [msgText, setMsgText] = useState('')
  const [sending, setSending] = useState(false)

  useEffect(() => { api.get('/api/clients/').then(r => setClients(r.data)) }, [])

  const toggleClient = async (id) => {
    if (expanded === id) { setExpanded(null); return }
    setExpanded(id)
    if (!orders[id]) {
      const r = await api.get(`/api/clients/${id}/orders`)
      setOrders(o => ({ ...o, [id]: r.data }))
    }
  }

  const openMsg = (e, client) => {
    e.stopPropagation()
    setMsgText('')
    setMsgModal({ userId: client.id, name: client.full_name || client.username || `ID ${client.telegram_id}` })
  }

  const sendMessage = async () => {
    if (!msgText.trim()) return
    setSending(true)
    try {
      await api.post(`/api/clients/${msgModal.userId}/message`, { text: msgText.trim() })
      toast.success('Сообщение отправлено')
      setMsgModal(null)
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Ошибка отправки')
    } finally {
      setSending(false)
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
              <div className="w-9 h-9 bg-ink-800 rounded-xl flex items-center justify-center text-sm font-semibold text-amber-400 shrink-0">
                {(client.full_name || client.username || '?')[0].toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium">{client.full_name || client.username || `ID ${client.telegram_id}`}</p>
                <p className="text-xs text-ink-500 mt-0.5">
                  {client.username ? `@${client.username}` : ''}{client.username && client.phone ? ' · ' : ''}{client.phone || ''}
                </p>
              </div>
              <p className="text-xs text-ink-500 shrink-0">{new Date(client.created_at).toLocaleDateString('ru')}</p>
              <button
                onClick={(e) => openMsg(e, client)}
                className="p-1.5 rounded-lg hover:bg-ink-700 text-ink-400 hover:text-amber-400 transition-colors shrink-0"
                title="Написать клиенту"
              >
                <Send size={14} />
              </button>
              <ChevronDown size={14} className={`text-ink-500 transition-transform shrink-0 ${expanded === client.id ? 'rotate-180' : ''}`} />
            </div>
            {expanded === client.id && orders[client.id] && (
              <div className="border-t border-ink-800 p-4">
                <div className="flex justify-between items-center mb-3">
                  <p className="text-xs text-ink-500 font-medium uppercase tracking-wide">История заказов</p>
                  <p className="text-sm font-mono text-amber-400">Итого: {orders[client.id].total_amount?.toFixed(0)} ₽</p>
                </div>
                {orders[client.id].orders?.length === 0 && (
                  <p className="text-sm text-ink-600">Заказов нет</p>
                )}
                <div className="space-y-1.5">
                  {orders[client.id].orders?.map(o => (
                    <div key={o.id} className="flex items-center justify-between bg-ink-800 rounded-lg px-3 py-2 text-sm">
                      <span className="font-mono text-amber-500">#{o.id}</span>
                      <span className="text-ink-400">{new Date(o.created_at).toLocaleDateString('ru')}</span>
                      <span className={STATUS_COLORS[o.status] || 'text-ink-300'}>{STATUS_LABELS[o.status] || o.status}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {msgModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="card w-full max-w-md p-6">
            <h2 className="text-lg font-semibold mb-1">Сообщение клиенту</h2>
            <p className="text-sm text-ink-500 mb-4">{msgModal.name}</p>
            <textarea
              className="input resize-none"
              rows={5}
              placeholder="Введите текст сообщения..."
              value={msgText}
              onChange={e => setMsgText(e.target.value)}
              autoFocus
            />
            <div className="flex gap-2 justify-end mt-4">
              <button className="btn-ghost" onClick={() => setMsgModal(null)}>Отмена</button>
              <button
                className="btn-primary flex items-center gap-2"
                onClick={sendMessage}
                disabled={sending || !msgText.trim()}
              >
                <Send size={14} /> {sending ? 'Отправка...' : 'Отправить'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
