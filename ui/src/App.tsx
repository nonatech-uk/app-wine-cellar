import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Shell from './components/layout/Shell.tsx'
import { usePageTracking } from './hooks/usePageTracking'
import Dashboard from './pages/Dashboard.tsx'
import Wines from './pages/Wines.tsx'
import WineDetail from './pages/WineDetail.tsx'
import Cellar from './pages/Cellar.tsx'
import Wishlist from './pages/Wishlist.tsx'

export default function App() {
  return (
    <BrowserRouter>
      <PageTracker />
      <Shell>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/wines" element={<Wines />} />
          <Route path="/wines/:id" element={<WineDetail />} />
          <Route path="/cellar" element={<Cellar />} />
          <Route path="/wishlist" element={<Wishlist />} />
          <Route path="*" element={<div className="text-text-secondary">Page not found</div>} />
        </Routes>
      </Shell>
    </BrowserRouter>
  )
}

function PageTracker() {
  usePageTracking()
  return null
}
