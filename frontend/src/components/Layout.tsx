import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import BottomNav from './BottomNav'
import MobileHeader from './MobileHeader'

export default function Layout() {
  return (
    <div className="flex min-h-screen bg-gray-50 dark:bg-slate-900">
      <Sidebar />
      <main className="flex-1 flex flex-col overflow-y-auto bg-gray-50 dark:bg-slate-900">
        <MobileHeader />
        {/* pb-20 clears the 64px BottomNav on mobile; md:pb-8 is required because pb-20 overrides md:p-8's bottom axis */}
        <div className="p-4 md:p-8 pb-20 md:pb-8">
          <Outlet />
        </div>
      </main>
      <BottomNav />
    </div>
  )
}
