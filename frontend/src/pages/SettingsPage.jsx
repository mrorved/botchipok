import { useEffect, useState } from 'react'
import api from '../api/client'
import toast from 'react-hot-toast'
import { Send, Trash2, Plus, Info, Pencil, Check, X } from 'lucide-react'

export default function SettingsPage() {
  const [admins, setAdmins] = useState([])
  const [newId, setNewId] = useState('')
  const [newLabel, setNewLabel] = useState('')
  const [adding, setAdding] = useState(false)
  const [testing, setTesting] = useState(false)
  const [pwForm, setPwForm] = useState({ old_password: '', new_password: '', confirm: '' })
  const [pwSaving, setPwSaving] = useState(false)
  const [editingId, setEditingId] = useState(null)
  const [editLabel, setEditLabel] = useState('')

  const load = () => api.get('/api/settings/notify-admins').then(r => setAdmins(r.data))
  useEffect(() => { load() }, [])

  const addAdmin = async () => {
    if (!newId.trim()) return
    const id = parseInt(newId.trim())
    if (isNaN(id)) { toast.error('Введите числовой Telegram ID'); return }
    setAdding(true)
    try {
      await api.post('/api/settings/notify-admins', { telegram_id: id, label: newLabel.trim() || null })
      toast.success('Администратор добавлен')
      setNewId(''); setNewLabel('')
      load()
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Ошибка')
    } finally {
      setAdding(false)
    }
  }

  const toggleActive = async (item) => {
    await api.patch(`/api/settings/notify-admins/${item.id}`, { label: item.label, is_active: !item.is_active })
    load()
  }

  const deleteAdmin = async (id) => {
    if (!confirm('Удалить получателя?')) return
    await api.delete(`/api/settings/notify-admins/${id}`)
    toast.success('Удалено')
    load()
  }

  const saveLabel = async (item) => {
    await api.patch(`/api/settings/notify-admins/${item.id}`, { label: editLabel.trim() || null, is_active: item.is_active })
    setEditingId(null)
    load()
  }

  const testNotify = async () => {
    setTesting(true)
    try {
      const r = await api.post('/api/settings/notify-admins/test')
      toast.success(`Тест отправлен: ${r.data.sent_to.join(', ')}`)
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Ошибка')
    } finally {
      setTesting(false)
    }
  }

  const changePassword = async () => {
    if (pwForm.new_password !== pwForm.confirm) {
      toast.error('Новые пароли не совпадают'); return
    }
    if (pwForm.new_password.length < 6) {
      toast.error('Минимум 6 символов'); return
    }
    setPwSaving(true)
    try {
      await api.post('/api/auth/change-password', {
        old_password: pwForm.old_password,
        new_password: pwForm.new_password,
      })
      toast.success('Пароль изменён')
      setPwForm({ old_password: '', new_password: '', confirm: '' })
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Ошибка')
    } finally {
      setPwSaving(false)
    }
  }

  const activeCount = admins.filter(a => a.is_active).length

  return (
    <div>
      <h1 className="text-xl font-semibold mb-6">Настройки</h1>

      <div className="card p-6 max-w-xl">
        <div className="flex items-center justify-between mb-1">
          <h2 className="text-sm font-semibold text-ink-300">Получатели уведомлений</h2>
          {activeCount > 0 && (
            <button
              onClick={testNotify}
              disabled={testing}
              className="flex items-center gap-1.5 text-xs text-ink-400 hover:text-amber-400 transition-colors"
            >
              <Send size={12} /> {testing ? 'Отправка...' : `Тест (${activeCount})`}
            </button>
          )}
        </div>
        <p className="text-xs text-ink-500 mb-5">
          Эти Telegram-аккаунты получают уведомления о новых заказах и сменах статуса.
        </p>

        {/* Список */}
        <div className="space-y-1.5 mb-5">
          {admins.length === 0 && (
            <p className="text-sm text-ink-600 py-2">Получателей нет</p>
          )}
          {admins.map(item => (
            <div key={item.id} className={`flex items-center gap-3 rounded-xl px-3 py-2.5 border transition-colors ${
              item.is_active ? 'bg-ink-800/60 border-ink-700' : 'bg-ink-900 border-ink-800 opacity-50'
            }`}>
              {/* Toggle active */}
              <button
                onClick={() => toggleActive(item)}
                className={`w-3 h-3 rounded-full shrink-0 border-2 transition-colors ${
                  item.is_active ? 'bg-emerald-400 border-emerald-400' : 'bg-transparent border-ink-500'
                }`}
                title={item.is_active ? 'Отключить' : 'Включить'}
              />
              <span className="font-mono text-sm text-amber-400 shrink-0">{item.telegram_id}</span>
              {editingId === item.id ? (
                <div className="flex items-center gap-1 flex-1">
                  <input
                    className="input py-1 text-sm flex-1"
                    value={editLabel}
                    onChange={e => setEditLabel(e.target.value)}
                    placeholder="Имя/пометка"
                    autoFocus
                  />
                  <button onClick={() => saveLabel(item)} className="p-1.5 rounded-lg bg-emerald-900/30 text-emerald-400 hover:bg-emerald-900/50">
                    <Check size={12} />
                  </button>
                  <button onClick={() => setEditingId(null)} className="p-1.5 rounded-lg hover:bg-ink-700 text-ink-400">
                    <X size={12} />
                  </button>
                </div>
              ) : (
                <>
                  <span className="text-sm text-ink-400 flex-1 truncate">{item.label || '—'}</span>
                  <button onClick={() => { setEditingId(item.id); setEditLabel(item.label || '') }}
                    className="p-1.5 rounded-lg hover:bg-ink-700 text-ink-500 hover:text-ink-200 transition-colors">
                    <Pencil size={12} />
                  </button>
                  <button onClick={() => deleteAdmin(item.id)}
                    className="p-1.5 rounded-lg hover:bg-red-900/30 text-ink-500 hover:text-red-400 transition-colors">
                    <Trash2 size={12} />
                  </button>
                </>
              )}
            </div>
          ))}
        </div>

        {/* Добавить нового */}
        <div className="border-t border-ink-800 pt-4">
          <p className="text-xs text-ink-400 font-medium mb-2">Добавить получателя</p>
          <div className="flex gap-2">
            <input
              className="input text-sm"
              placeholder="Telegram ID (число)"
              value={newId}
              onChange={e => setNewId(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && addAdmin()}
            />
            <input
              className="input text-sm"
              placeholder="Имя (необязательно)"
              value={newLabel}
              onChange={e => setNewLabel(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && addAdmin()}
            />
            <button
              onClick={addAdmin}
              disabled={adding || !newId.trim()}
              className="btn-primary flex items-center gap-1.5 shrink-0"
            >
              <Plus size={14} /> {adding ? '...' : 'Добавить'}
            </button>
          </div>
        </div>

        {/* Подсказка */}
        <div className="mt-4 bg-ink-800/40 border border-ink-700/50 rounded-xl p-3 flex items-start gap-2">
          <Info size={13} className="text-amber-400 mt-0.5 shrink-0" />
          <p className="text-xs text-ink-500">
            Узнать свой Telegram ID можно у бота <span className="text-ink-300">@userinfobot</span>. 
            Зелёная точка — уведомления включены, серая — отключены.
          </p>
        </div>
      </div>

      {/* Смена пароля */}
      <div className="card p-6 max-w-xl mt-4">
        <h2 className="text-sm font-semibold text-ink-300 mb-1">Смена пароля</h2>
        <p className="text-xs text-ink-500 mb-5">Пароль для входа в панель администратора.</p>
        <div className="space-y-3">
          <div>
            <label className="text-xs text-ink-400 font-medium mb-1.5 block">Текущий пароль</label>
            <input
              type="password"
              className="input"
              placeholder="••••••••"
              value={pwForm.old_password}
              onChange={e => setPwForm(f => ({ ...f, old_password: e.target.value }))}
            />
          </div>
          <div>
            <label className="text-xs text-ink-400 font-medium mb-1.5 block">Новый пароль</label>
            <input
              type="password"
              className="input"
              placeholder="Минимум 6 символов"
              value={pwForm.new_password}
              onChange={e => setPwForm(f => ({ ...f, new_password: e.target.value }))}
            />
          </div>
          <div>
            <label className="text-xs text-ink-400 font-medium mb-1.5 block">Повторите новый пароль</label>
            <input
              type="password"
              className="input"
              placeholder="••••••••"
              value={pwForm.confirm}
              onChange={e => setPwForm(f => ({ ...f, confirm: e.target.value }))}
            />
          </div>
        </div>
        <div className="flex justify-end mt-4">
          <button
            className="btn-primary"
            onClick={changePassword}
            disabled={pwSaving || !pwForm.old_password || !pwForm.new_password || !pwForm.confirm}
          >
            {pwSaving ? 'Сохранение...' : 'Сменить пароль'}
          </button>
        </div>
      </div>
    </div>
  )
}
