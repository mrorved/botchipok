import { useEffect, useState, useRef } from 'react'
import api from '../api/client'
import toast from 'react-hot-toast'
import { Plus, Pencil, Trash2, Upload, Eye, EyeOff } from 'lucide-react'

const emptyForm = { name: '', description: '', price: '', unit: '', weight: '', photo_url: '', category_id: '', is_visible: true }

export default function ProductsPage() {
  const [products, setProducts] = useState([])
  const [categories, setCategories] = useState([])
  const [modal, setModal] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const [editId, setEditId] = useState(null)
  const fileRef = useRef()

  const load = async () => {
    const [p, c] = await Promise.all([
      api.get('/api/products/'),
      api.get('/api/categories/all'),
    ])
    setProducts(p.data)
    setCategories(c.data)
  }

  useEffect(() => { load() }, [])

  const openCreate = () => { setForm(emptyForm); setEditId(null); setModal('form') }
  const openEdit = (p) => {
    setForm({ ...p, category_id: p.category_id || '', price: String(p.price), unit: p.unit || '', weight: p.weight || '' })
    setEditId(p.id)
    setModal('form')
  }

  const submit = async () => {
    const body = { ...form, price: parseFloat(form.price), category_id: form.category_id || null, unit: form.unit || null, weight: form.weight || null }
    try {
      if (editId) await api.put(`/api/products/${editId}`, body)
      else await api.post('/api/products/', body)
      toast.success(editId ? 'Товар обновлён' : 'Товар создан')
      setModal(null)
      load()
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Ошибка')
    }
  }

  const del = async (id) => {
    if (!confirm('Удалить товар?')) return
    try {
      const r = await api.delete(`/api/products/${id}`)
      if (r.data.orders_affected > 0) {
        toast(r.data.message, { icon: '⚠️', duration: 5000 })
      } else {
        toast.success('Товар удалён')
      }
      load()
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Ошибка удаления')
    }
  }

  const toggleVisible = async (p) => {
    await api.put(`/api/products/${p.id}`, { ...p, is_visible: !p.is_visible })
    load()
  }

  const importFile = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    const fd = new FormData()
    fd.append('file', file)
    try {
      const r = await api.post('/api/products/import', fd)
      const d = r.data
      let msg = `Импортировано: ${d.imported} товаров`
      if (d.categories_created > 0) msg += `, создано категорий: ${d.categories_created}`
      if (d.skipped > 0) msg += ` (пропущено: ${d.skipped})`
      toast.success(msg, { duration: 5000 })
      load()
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Ошибка импорта')
    }
    e.target.value = ''
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold">Товары</h1>
        <div className="flex gap-2">
          <input ref={fileRef} type="file" accept=".xlsx,.csv" className="hidden" onChange={importFile} />
          <button
            onClick={() => fileRef.current.click()}
            className="btn-ghost flex items-center gap-2"
            title="Поддерживается формат с колонками: Наименование, Цена, Раздел 1/2, Активно, Изображение, Описание"
          >
            <Upload size={14} /> Импорт
          </button>
          <button onClick={openCreate} className="btn-primary flex items-center gap-2">
            <Plus size={14} /> Добавить
          </button>
        </div>
      </div>

      <div className="card overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-ink-800 text-left">
              <th className="px-4 py-3 text-xs text-ink-500 font-medium">Название</th>
              <th className="px-4 py-3 text-xs text-ink-500 font-medium">Категория</th>
              <th className="px-4 py-3 text-xs text-ink-500 font-medium">Цена</th>
              <th className="px-4 py-3 text-xs text-ink-500 font-medium">Ед. изм.</th>
              <th className="px-4 py-3 text-xs text-ink-500 font-medium">Фасовка</th>
              <th className="px-4 py-3 text-xs text-ink-500 font-medium">Видим</th>
              <th className="px-4 py-3 w-24"></th>
            </tr>
          </thead>
          <tbody>
            {products.map((p, i) => (
              <tr key={p.id} className={`border-b border-ink-800/50 hover:bg-ink-800/30 transition-colors ${i === products.length - 1 ? 'border-b-0' : ''}`}>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-3">
                    {p.photo_url && (
                      <img src={p.photo_url} alt="" className="w-8 h-8 rounded-lg object-cover bg-ink-800" onError={e => e.target.style.display='none'} />
                    )}
                    <span className="font-medium text-ink-200">{p.name}</span>
                  </div>
                </td>
                <td className="px-4 py-3 text-ink-500">{p.category?.name || '—'}</td>
                <td className="px-4 py-3 font-mono text-amber-400">{p.price} ₽</td>
                <td className="px-4 py-3 text-ink-500 text-xs">{p.unit || '—'}</td>
                <td className="px-4 py-3 text-ink-500 text-xs">{p.weight || '—'}</td>
                <td className="px-4 py-3">
                  <button onClick={() => toggleVisible(p)} className="text-ink-500 hover:text-ink-200 transition-colors">
                    {p.is_visible ? <Eye size={15} /> : <EyeOff size={15} />}
                  </button>
                </td>
                <td className="px-4 py-3">
                  <div className="flex gap-1 justify-end">
                    <button onClick={() => openEdit(p)} className="p-1.5 rounded-lg hover:bg-ink-700 text-ink-400 hover:text-ink-200 transition-colors">
                      <Pencil size={13} />
                    </button>
                    <button onClick={() => del(p.id)} className="p-1.5 rounded-lg hover:bg-red-900/30 text-ink-400 hover:text-red-400 transition-colors">
                      <Trash2 size={13} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {products.length === 0 && (
              <tr><td colSpan={7} className="px-4 py-10 text-center text-ink-500">Товаров нет</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {modal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="card w-full max-w-md p-6">
            <h2 className="text-lg font-semibold mb-5">{editId ? 'Редактировать товар' : 'Новый товар'}</h2>
            <div className="space-y-3">
              <Field label="Название *">
                <input className="input" value={form.name} onChange={e => setForm(f => ({...f, name: e.target.value}))} />
              </Field>
              <Field label="Описание">
                <textarea className="input resize-none" rows={3} value={form.description} onChange={e => setForm(f => ({...f, description: e.target.value}))} />
              </Field>
              <div className="grid grid-cols-2 gap-3">
                <Field label="Цена *">
                  <input className="input" type="number" value={form.price} onChange={e => setForm(f => ({...f, price: e.target.value}))} />
                </Field>
                <Field label="Ед. изм.">
                  <input className="input" placeholder="шт., кг, л, уп." value={form.unit} onChange={e => setForm(f => ({...f, unit: e.target.value}))} />
                </Field>
              </div>
              <Field label="Фасовка / Вес">
                <input className="input" placeholder="1.5 кг, 500 мл, 2 шт." value={form.weight} onChange={e => setForm(f => ({...f, weight: e.target.value}))} />
              </Field>
              <Field label="Категория">
                <select className="input" value={form.category_id} onChange={e => setForm(f => ({...f, category_id: e.target.value}))}>
                  <option value="">— Нет —</option>
                  {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </Field>
              <Field label="URL фото">
                <input className="input" placeholder="https://..." value={form.photo_url} onChange={e => setForm(f => ({...f, photo_url: e.target.value}))} />
              </Field>
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" className="accent-amber-500" checked={form.is_visible} onChange={e => setForm(f => ({...f, is_visible: e.target.checked}))} />
                <span className="text-sm text-ink-300">Видимый</span>
              </label>
            </div>
            <div className="flex gap-2 justify-end mt-6">
              <button className="btn-ghost" onClick={() => setModal(null)}>Отмена</button>
              <button className="btn-primary" onClick={submit}>Сохранить</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function Field({ label, children }) {
  return (
    <div>
      <label className="text-xs text-ink-400 font-medium mb-1.5 block">{label}</label>
      {children}
    </div>
  )
}
