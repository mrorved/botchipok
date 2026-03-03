import { useEffect, useState } from 'react'
import api from '../api/client'
import toast from 'react-hot-toast'
import { Download, ChevronDown, Trash2, Pencil, X, Check, Package, Send } from 'lucide-react'
import { downloadFile } from '../utils/download'

const STATUS_LABELS = {
  pending: 'На подтверждении',
  confirmed: 'Подтверждён',
  adjusted: 'С корректировкой',
  paid: 'Оплачен',
  issued: 'Выдан',
  cancelled: 'Отменён',
}

const STATUS_TRANSITIONS = {
  pending: ['confirmed', 'adjusted', 'cancelled'],
  confirmed: ['adjusted', 'paid', 'cancelled'],
  adjusted: ['paid', 'cancelled'],
  paid: ['issued'],
  issued: [],
  cancelled: [],
}

const STATUS_COLORS = {
  pending:   'bg-yellow-500/15 text-yellow-400 border-yellow-800/50',
  confirmed: 'bg-blue-500/15 text-blue-400 border-blue-800/50',
  adjusted:  'bg-purple-500/15 text-purple-400 border-purple-800/50',
  paid:      'bg-emerald-500/15 text-emerald-400 border-emerald-800/50',
  issued:    'bg-ink-700 text-ink-400 border-ink-600',
  cancelled: 'bg-red-500/15 text-red-400 border-red-800/50',
}

const TABS = [
  { key: 'active', label: 'Активные' },
  { key: 'pending', label: 'На подтверждении' },
  { key: 'confirmed', label: 'Подтверждён' },
  { key: 'adjusted', label: 'С корректировкой' },
  { key: 'paid', label: 'Оплачен' },
  { key: 'issued', label: 'Выдан' },
  { key: 'cancelled', label: 'Отменён' },
]

const ACTIVE_STATUSES = ['pending', 'confirmed', 'adjusted', 'paid']
const DELETABLE_STATUSES = ['cancelled', 'issued']

export default function OrdersPage() {
  const [orders, setOrders] = useState([])
  const [tab, setTab] = useState('active')
  const [expanded, setExpanded] = useState(null)
  const [editingItem, setEditingItem] = useState(null)
  const [editQty, setEditQty] = useState(1)
  const [broadcastModal, setBroadcastModal] = useState(false)
  const [broadcastText, setBroadcastText] = useState('')
  const [broadcasting, setBroadcasting] = useState(false)

  const load = async () => {
    const params = tab === 'active' ? '' : `?status=${tab}`
    const r = await api.get(`/api/orders/${params}`)
    let data = r.data
    if (tab === 'active') data = data.filter(o => ACTIVE_STATUSES.includes(o.status))
    setOrders(data)
  }

  useEffect(() => { load() }, [tab])

  const changeStatus = async (orderId, newStatus) => {
    if (newStatus === 'cancelled' && !confirm('Отменить заказ? Клиент получит уведомление.')) return
    try {
      await api.patch(`/api/orders/${orderId}/status`, { status: newStatus })
      toast.success('Статус обновлён')
      setExpanded(null)
      load()
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Ошибка')
    }
  }

  const deleteOrder = async (orderId, status) => {
    const label = STATUS_LABELS[status]
    if (!confirm(`Удалить заказ #${orderId} (${label})? Это действие необратимо.`)) return
    try {
      await api.delete(`/api/orders/${orderId}`)
      toast.success(`Заказ #${orderId} удалён`)
      setExpanded(null)
      load()
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Ошибка удаления')
    }
  }

  const deleteItem = async (orderId, itemId) => {
    if (!confirm('Удалить позицию?')) return
    try {
      await api.delete(`/api/orders/${orderId}/items/${itemId}`)
      toast.success('Удалено')
      load()
    } catch (e) {
      toast.error('Ошибка')
    }
  }

  const saveEditItem = async () => {
    const { orderId, itemId } = editingItem
    try {
      await api.patch(`/api/orders/${orderId}/items/${itemId}`, { quantity: Number(editQty) })
      toast.success('Обновлено')
      setEditingItem(null)
      load()
    } catch (e) {
      toast.error('Ошибка')
    }
  }

  const exportOrder = async (orderId, format = 'xlsx') => {
    try {
      await downloadFile(`/api/orders/${orderId}/export?format=${format}`, `order_${orderId}.${format}`)
    } catch {
      toast.error('Ошибка скачивания')
    }
  }

  const exportPendingSummary = async (format = 'xlsx') => {
    try {
      await downloadFile(`/api/orders/export/pending?format=${format}`, `pending_orders.${format}`)
    } catch {
      toast.error('Ошибка скачивания')
    }
  }

  const canEdit = (status) => ACTIVE_STATUSES.includes(status)

  const sendBroadcast = async () => {
    if (!broadcastText.trim()) return
    setBroadcasting(true)
    try {
      const r = await api.post('/api/clients/broadcast/active-orders', { text: broadcastText.trim() })
      toast.success(`Отправлено ${r.data.sent} клиентам${r.data.failed > 0 ? `, ошибок: ${r.data.failed}` : ''}`)
      setBroadcastModal(false)
      setBroadcastText('')
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Ошибка рассылки')
    } finally {
      setBroadcasting(false)
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold">Заказы</h1>
        <div className="flex gap-2">
          <button
            onClick={() => exportPendingSummary('xlsx')}
            className="btn-ghost flex items-center gap-2 text-xs"
            title="Сводный список товаров из заказов «На подтверждении»"
          >
            <Package size={14} /> Сводная выгрузка
          </button>
          <button
            onClick={() => { setBroadcastText(''); setBroadcastModal(true) }}
            className="btn-ghost flex items-center gap-2 text-xs"
            title="Отправить сообщение клиентам с активными заказами"
          >
            <Send size={14} /> Рассылка
          </button>
        </div>
      </div>

      {/* Вкладки */}
      <div className="flex gap-1 mb-5 overflow-x-auto pb-1">
        {TABS.map(t => (
          <button
            key={t.key}
            onClick={() => { setTab(t.key); setExpanded(null) }}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all border shrink-0 ${
              tab === t.key
                ? t.key === 'active'
                  ? 'bg-amber-500/10 text-amber-400 border-amber-800/50'
                  : STATUS_COLORS[t.key]
                : 'text-ink-400 border-ink-800 hover:border-ink-700'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="space-y-2">
        {orders.length === 0 && (
          <div className="card p-10 text-center text-ink-500 text-sm">Заказов нет</div>
        )}
        {orders.map(order => (
          <div key={order.id} className="card overflow-hidden">
            {/* Заголовок */}
            <div
              className="flex items-center gap-4 p-4 cursor-pointer hover:bg-ink-800/30 transition-colors"
              onClick={() => setExpanded(expanded === order.id ? null : order.id)}
            >
              <span className="font-mono text-amber-500 text-sm font-medium w-16">#{order.id}</span>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">
                  {order.user?.full_name || order.user?.username || `tg:${order.user?.telegram_id}`}
                  {order.user?.username && <span className="text-ink-500 font-normal"> @{order.user.username}</span>}
                </p>
                <p className="text-xs text-ink-500 mt-0.5 flex items-center gap-2">
                  <span>{new Date(order.created_at).toLocaleString('ru')}</span>
                  {order.user?.phone && <span className="text-amber-500/70">📞 {order.user.phone}</span>}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <span className={`badge border text-xs ${STATUS_COLORS[order.status]}`}>
                  {STATUS_LABELS[order.status]}
                </span>
                <span className="text-xs font-mono text-amber-400">
                  {order.items?.reduce((s, i) => s + i.price_at_order * i.quantity, 0).toFixed(0)} ₽
                </span>
              </div>
              <ChevronDown size={14} className={`text-ink-500 transition-transform shrink-0 ${expanded === order.id ? 'rotate-180' : ''}`} />
            </div>

            {/* Детали */}
            {expanded === order.id && (
              <div className="border-t border-ink-800 p-4 space-y-4">

                <div className="flex justify-between items-center">
                  <p className="text-xs text-ink-500 font-medium uppercase tracking-wide">Товары</p>
                  <div className="flex gap-1.5">
                    <button
                      onClick={() => exportOrder(order.id, 'xlsx')}
                      className="flex items-center gap-1 text-xs text-ink-400 hover:text-ink-200 border border-ink-700 hover:border-ink-600 rounded-lg px-2 py-1 transition-colors"
                    >
                      <Download size={11} /> Excel
                    </button>
                    <button
                      onClick={() => exportOrder(order.id, 'csv')}
                      className="flex items-center gap-1 text-xs text-ink-400 hover:text-ink-200 border border-ink-700 hover:border-ink-600 rounded-lg px-2 py-1 transition-colors"
                    >
                      <Download size={11} /> CSV
                    </button>
                  </div>
                </div>

                {/* Позиции */}
                <div className="space-y-1.5">
                  {order.items?.map(item => (
                    <div key={item.id} className="flex items-center gap-3 bg-ink-800/50 rounded-lg px-3 py-2">
                      <span className="text-sm text-ink-300 flex-1">
                        {item.product?.name || <span className="text-ink-600 italic">Удалённый товар</span>}
                      </span>

                      {editingItem?.orderId === order.id && editingItem?.itemId === item.id ? (
                        <div className="flex items-center gap-1">
                          <input
                            type="number" min="1" value={editQty}
                            onChange={e => setEditQty(e.target.value)}
                            className="input w-16 py-1 text-center text-sm"
                            onClick={e => e.stopPropagation()}
                          />
                          <button onClick={saveEditItem} className="p-1.5 rounded-lg bg-emerald-900/30 text-emerald-400 hover:bg-emerald-900/50">
                            <Check size={13} />
                          </button>
                          <button onClick={() => setEditingItem(null)} className="p-1.5 rounded-lg hover:bg-ink-700 text-ink-400">
                            <X size={13} />
                          </button>
                        </div>
                      ) : (
                        <span className="text-sm font-mono text-ink-400">× {item.quantity}</span>
                      )}

                      <span className="text-sm font-mono text-amber-400 w-20 text-right">
                        {(item.price_at_order * item.quantity).toFixed(0)} ₽
                      </span>

                      {canEdit(order.status) && editingItem?.itemId !== item.id && (
                        <div className="flex gap-1">
                          <button
                            onClick={() => { setEditingItem({ orderId: order.id, itemId: item.id }); setEditQty(item.quantity) }}
                            className="p-1.5 rounded-lg hover:bg-ink-700 text-ink-500 hover:text-ink-200 transition-colors"
                          >
                            <Pencil size={12} />
                          </button>
                          <button
                            onClick={() => deleteItem(order.id, item.id)}
                            className="p-1.5 rounded-lg hover:bg-red-900/30 text-ink-500 hover:text-red-400 transition-colors"
                          >
                            <Trash2 size={12} />
                          </button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                <div className="flex justify-end">
                  <span className="text-sm font-mono text-amber-400 font-semibold">
                    Итого: {order.items?.reduce((s, i) => s + i.price_at_order * i.quantity, 0).toFixed(0)} ₽
                  </span>
                </div>

                {/* Комментарий */}
                {order.comment && (
                  <div>
                    <p className="text-xs text-ink-500 font-medium mb-1 uppercase tracking-wide">Комментарий</p>
                    <p className="text-sm text-ink-300 bg-ink-800 rounded-lg px-3 py-2">{order.comment}</p>
                  </div>
                )}

                {/* Смена статуса */}
                {STATUS_TRANSITIONS[order.status]?.length > 0 && (
                  <div>
                    <p className="text-xs text-ink-500 font-medium mb-2 uppercase tracking-wide">Действия</p>
                    <div className="flex gap-2 flex-wrap">
                      {STATUS_TRANSITIONS[order.status].map(s => (
                        <button key={s} onClick={() => changeStatus(order.id, s)}
                          className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                            s === 'cancelled'
                              ? 'bg-red-900/20 text-red-400 border-red-800/50 hover:bg-red-900/40'
                              : STATUS_COLORS[s] + ' hover:opacity-80'
                          }`}>
                          {s === 'cancelled' ? '✕ Отменить' : `→ ${STATUS_LABELS[s]}`}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Удаление заказа — только для выданных и отменённых */}
                {DELETABLE_STATUSES.includes(order.status) && (
                  <div className="pt-2 border-t border-ink-800/50 flex justify-end">
                    <button
                      onClick={() => deleteOrder(order.id, order.status)}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-red-400 border border-red-900/50 hover:bg-red-900/20 transition-colors"
                    >
                      <Trash2 size={12} /> Удалить заказ
                    </button>
                  </div>
                )}

              </div>
            )}
          </div>
        ))}
      </div>
      {broadcastModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="card w-full max-w-md p-6">
            <h2 className="text-lg font-semibold mb-1">Рассылка по активным заказам</h2>
            <p className="text-sm text-ink-500 mb-4">Сообщение получат все клиенты у которых есть заказы со статусом: на подтверждении, подтверждён, с корректировкой или оплачен.</p>
            <textarea
              className="input resize-none"
              rows={5}
              placeholder="Введите текст сообщения..."
              value={broadcastText}
              onChange={e => setBroadcastText(e.target.value)}
              autoFocus
            />
            <div className="flex gap-2 justify-end mt-4">
              <button className="btn-ghost" onClick={() => setBroadcastModal(false)}>Отмена</button>
              <button
                className="btn-primary flex items-center gap-2"
                onClick={sendBroadcast}
                disabled={broadcasting || !broadcastText.trim()}
              >
                <Send size={14} /> {broadcasting ? 'Отправка...' : 'Отправить'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
