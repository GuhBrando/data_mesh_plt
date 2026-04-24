import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import BottomNav from './BottomNav'

export default function Layout() {
  return (
    <div className="flex min-h-screen bg-gray-50 dark:bg-slate-900">
      <Sidebar />
      <main className="flex-1 overflow-y-auto bg-gray-50 dark:bg-slate-900">
        <div className="p-4 md:p-8 pb-20 md:pb-8">
          <Outlet />
        </div>
      </main>
      <BottomNav />
    </div>
  )
}
