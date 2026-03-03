import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import {
  LayoutDashboard, Package, Tag, ShoppingCart, Users, LogOut, Settings
} from 'lucide-react'

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Дашборд' },
  { to: '/orders', icon: ShoppingCart, label: 'Заказы' },
  { to: '/products', icon: Package, label: 'Товары' },
  { to: '/categories', icon: Tag, label: 'Категории' },
  { to: '/clients', icon: Users, label: 'Клиенты' },
]

export default function Layout() {
  const { logout } = useAuth()
  const navigate = useNavigate()
  const handleLogout = () => { logout(); navigate('/login') }

  return (
    <div className="flex h-screen overflow-hidden">
      <aside className="w-56 bg-ink-900 border-r border-ink-800 flex flex-col shrink-0">
        <div className="p-5 border-b border-ink-800">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 bg-amber-500 rounded-lg flex items-center justify-center">
              <Package size={14} className="text-ink-950" />
            </div>
            <span className="font-semibold text-ink-100">ShopAdmin</span>
          </div>
        </div>

        <nav className="flex-1 p-3 space-y-0.5">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all ${
                  isActive
                    ? 'bg-amber-500/10 text-amber-400 font-medium'
                    : 'text-ink-400 hover:text-ink-100 hover:bg-ink-800'
                }`
              }
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="p-3 border-t border-ink-800 space-y-0.5">
          <NavLink
            to="/settings"
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all w-full ${
                isActive
                  ? 'bg-amber-500/10 text-amber-400 font-medium'
                  : 'text-ink-400 hover:text-ink-100 hover:bg-ink-800'
              }`
            }
          >
            <Settings size={16} />
            Настройки
          </NavLink>
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-ink-400 hover:text-red-400 hover:bg-red-900/20 transition-all w-full"
          >
            <LogOut size={16} />
            Выйти
          </button>
        </div>
      </aside>

      <main className="flex-1 overflow-auto bg-ink-950">
        <div className="p-6 max-w-7xl mx-auto">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
