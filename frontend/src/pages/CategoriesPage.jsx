import { useEffect, useState } from 'react'
import api from '../api/client'
import toast from 'react-hot-toast'
import { Plus, Pencil, Trash2, Eye, EyeOff } from 'lucide-react'

const emptyForm = { name: '', parent_id: '', is_visible: true }

export default function CategoriesPage() {
  const [categories, setCategories] = useState([])
  const [modal, setModal] = useState(false)
  const [form, setForm] = useState(emptyForm)
  const [editId, setEditId] = useState(null)

  const load = () => api.get('/api/categories/all').then(r => setCategories(r.data))
  useEffect(() => { load() }, [])

  const flat = categories.filter(c => !c.parent_id)

  const submit = async () => {
    const body = { ...form, parent_id: form.parent_id ? parseInt(form.parent_id) : null }
    try {
      if (editId) await api.put(`/api/categories/${editId}`, body)
      else await api.post('/api/categories/', body)
      toast.success('Сохранено')
      setModal(false)
      load()
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Ошибка')
    }
  }

  const del = async (id) => {
    if (!confirm('Удалить категорию?')) return
    await api.delete(`/api/categories/${id}`)
    toast.success('Удалено')
    load()
  }

  const openEdit = (c) => {
    setForm({ name: c.name, parent_id: c.parent_id || '', is_visible: c.is_visible })
    setEditId(c.id)
    setModal(true)
  }

  const openCreate = () => { setForm(emptyForm); setEditId(null); setModal(true) }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold">Категории</h1>
        <button onClick={openCreate} className="btn-primary flex items-center gap-2">
          <Plus size={14} /> Добавить
        </button>
      </div>

      <div className="card overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-ink-800">
              <th className="px-4 py-3 text-xs text-ink-500 font-medium text-left">Название</th>
              <th className="px-4 py-3 text-xs text-ink-500 font-medium text-left">Родитель</th>
              <th className="px-4 py-3 text-xs text-ink-500 font-medium text-left">Подкатегории</th>
              <th className="px-4 py-3 text-xs text-ink-500 font-medium text-left">Видима</th>
              <th className="px-4 py-3 w-20"></th>
            </tr>
          </thead>
          <tbody>
            {categories.map((c, i) => {
              const parent = categories.find(p => p.id === c.parent_id)
              return (
                <tr key={c.id} className={`border-b border-ink-800/50 hover:bg-ink-800/30 transition-colors ${i === categories.length-1 ? 'border-b-0' : ''}`}>
                  <td className="px-4 py-3 text-ink-200 font-medium">{c.name}</td>
                  <td className="px-4 py-3 text-ink-500">{parent?.name || '—'}</td>
                  <td className="px-4 py-3 text-ink-500">{c.children?.length || 0}</td>
                  <td className="px-4 py-3">
                    {c.is_visible
                      ? <Eye size={15} className="text-emerald-400" />
                      : <EyeOff size={15} className="text-ink-600" />}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-1 justify-end">
                      <button onClick={() => openEdit(c)} className="p-1.5 rounded-lg hover:bg-ink-700 text-ink-400 hover:text-ink-200 transition-colors">
                        <Pencil size={13} />
                      </button>
                      <button onClick={() => del(c.id)} className="p-1.5 rounded-lg hover:bg-red-900/30 text-ink-400 hover:text-red-400 transition-colors">
                        <Trash2 size={13} />
                      </button>
                    </div>
                  </td>
                </tr>
              )
            })}
            {categories.length === 0 && (
              <tr><td colSpan={5} className="px-4 py-10 text-center text-ink-500">Категорий нет</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {modal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="card w-full max-w-sm p-6">
            <h2 className="text-lg font-semibold mb-5">{editId ? 'Редактировать' : 'Новая категория'}</h2>
            <div className="space-y-3">
              <div>
                <label className="text-xs text-ink-400 font-medium mb-1.5 block">Название *</label>
                <input className="input" value={form.name} onChange={e => setForm(f => ({...f, name: e.target.value}))} />
              </div>
              <div>
                <label className="text-xs text-ink-400 font-medium mb-1.5 block">Родительская категория</label>
                <select className="input" value={form.parent_id} onChange={e => setForm(f => ({...f, parent_id: e.target.value}))}>
                  <option value="">— Корневая —</option>
                  {flat.filter(c => c.id !== editId).map(c => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" className="accent-amber-500" checked={form.is_visible} onChange={e => setForm(f => ({...f, is_visible: e.target.checked}))} />
                <span className="text-sm text-ink-300">Видимая</span>
              </label>
            </div>
            <div className="flex gap-2 justify-end mt-6">
              <button className="btn-ghost" onClick={() => setModal(false)}>Отмена</button>
              <button className="btn-primary" onClick={submit}>Сохранить</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
