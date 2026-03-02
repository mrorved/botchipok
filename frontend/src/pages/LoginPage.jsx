import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Package } from 'lucide-react'
import toast from 'react-hot-toast'

export default function LoginPage() {
  const { login, loading, isAuth } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ username: '', password: '' })

  if (isAuth) { navigate('/dashboard'); return null }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const ok = await login(form.username, form.password)
    if (ok) navigate('/dashboard')
    else toast.error('Неверный логин или пароль')
  }

  return (
    <div className="min-h-screen bg-ink-950 flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="flex items-center justify-center gap-3 mb-8">
          <div className="w-10 h-10 bg-amber-500 rounded-xl flex items-center justify-center">
            <Package size={20} className="text-ink-950" />
          </div>
          <span className="text-xl font-semibold text-ink-100">ShopAdmin</span>
        </div>

        <div className="card p-6">
          <h1 className="text-lg font-semibold text-ink-100 mb-1">Вход</h1>
          <p className="text-sm text-ink-500 mb-6">Панель администратора</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-xs text-ink-400 font-medium mb-1.5 block">Логин</label>
              <input
                className="input"
                placeholder="admin"
                value={form.username}
                onChange={e => setForm(f => ({ ...f, username: e.target.value }))}
                required
              />
            </div>
            <div>
              <label className="text-xs text-ink-400 font-medium mb-1.5 block">Пароль</label>
              <input
                className="input"
                type="password"
                placeholder="••••••••"
                value={form.password}
                onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
                required
              />
            </div>
            <button type="submit" className="btn-primary w-full mt-2" disabled={loading}>
              {loading ? 'Вход...' : 'Войти'}
            </button>
          </form>
        </div>

        <p className="text-center text-xs text-ink-600 mt-4">
          По умолчанию: admin / admin123
        </p>
      </div>
    </div>
  )
}
