import AppShell from '@/components/layout/AppShell'
import AdminPage from './page'

export const metadata = { title: 'Admin Panel — BrahmaAI' }

export default function AdminLayout() {
  return (
    <AppShell>
      <AdminPage />
    </AppShell>
  )
}
