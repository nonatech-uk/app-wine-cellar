import { Link } from 'react-router-dom'
import { useCellar, useUpdateCellar } from '../hooks/useWines.ts'
import LoadingSpinner from '../components/common/LoadingSpinner.tsx'
import StatCard from '../components/common/StatCard.tsx'

export default function Cellar() {
  const { data: cellar, isLoading } = useCellar()
  const updateCellar = useUpdateCellar()

  if (isLoading) return <LoadingSpinner />

  const totalBottles = cellar?.reduce((sum, c) => sum + c.quantity, 0) ?? 0
  const locations = [...new Set(cellar?.map(c => c.storage_location).filter(Boolean) ?? [])]

  const handleQuantityChange = (id: number, delta: number, current: number) => {
    const newQty = Math.max(0, current + delta)
    updateCellar.mutate({ id, data: { quantity: newQty } })
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold">Cellar</h2>

      <div className="grid grid-cols-2 gap-4 max-w-md">
        <StatCard label="Total Bottles" value={totalBottles} />
        <StatCard label="Locations" value={locations.length || 'Unassigned'} />
      </div>

      <div className="bg-bg-card border border-border rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-bg-primary">
              <th className="text-left px-4 py-2 font-medium text-text-secondary">Wine</th>
              <th className="text-left px-4 py-2 font-medium text-text-secondary w-16">Year</th>
              <th className="text-left px-4 py-2 font-medium text-text-secondary">Type</th>
              <th className="text-left px-4 py-2 font-medium text-text-secondary">Location</th>
              <th className="text-center px-4 py-2 font-medium text-text-secondary w-32">Quantity</th>
            </tr>
          </thead>
          <tbody>
            {cellar?.map(item => (
              <tr key={item.id} className="border-b border-border last:border-0 hover:bg-bg-hover">
                <td className="px-4 py-2">
                  <Link to={`/wines/${item.wine_id}`} className="text-accent hover:underline">
                    {item.wine_producer} {item.wine_name}
                  </Link>
                </td>
                <td className="px-4 py-2 tabular-nums text-text-secondary">{item.wine_vintage || '-'}</td>
                <td className="px-4 py-2 text-text-secondary">{item.wine_type || '-'}</td>
                <td className="px-4 py-2 text-text-secondary">{item.storage_location || '-'}</td>
                <td className="px-4 py-2">
                  <div className="flex items-center justify-center gap-2">
                    <button
                      onClick={() => handleQuantityChange(item.id, -1, item.quantity)}
                      className="w-6 h-6 flex items-center justify-center rounded border border-border hover:bg-bg-hover text-text-secondary"
                    >
                      -
                    </button>
                    <span className="tabular-nums font-medium w-6 text-center">{item.quantity}</span>
                    <button
                      onClick={() => handleQuantityChange(item.id, 1, item.quantity)}
                      className="w-6 h-6 flex items-center justify-center rounded border border-border hover:bg-bg-hover text-text-secondary"
                    >
                      +
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {(!cellar || cellar.length === 0) && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-text-secondary">
                  No wines in cellar
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
