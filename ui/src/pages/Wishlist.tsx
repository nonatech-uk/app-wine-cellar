import { Link } from 'react-router-dom'
import { useWishlist, useUpdateWishlist, useDeleteWishlist } from '../hooks/useWines.ts'
import LoadingSpinner from '../components/common/LoadingSpinner.tsx'

export default function Wishlist() {
  const { data: wishlist, isLoading } = useWishlist()
  const updateWishlist = useUpdateWishlist()
  const deleteWishlist = useDeleteWishlist()

  if (isLoading) return <LoadingSpinner />

  const active = wishlist?.filter(w => !w.acquired) ?? []
  const acquired = wishlist?.filter(w => w.acquired) ?? []

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold">Wishlist</h2>

      <div className="bg-bg-card border border-border rounded-lg overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-bg-primary">
              <th className="text-left px-4 py-2 font-medium text-text-secondary">Wine</th>
              <th className="text-left px-4 py-2 font-medium text-text-secondary w-16">Year</th>
              <th className="text-left px-4 py-2 font-medium text-text-secondary">Notes</th>
              <th className="text-left px-4 py-2 font-medium text-text-secondary w-28">Added</th>
              <th className="text-center px-4 py-2 font-medium text-text-secondary w-24">Actions</th>
            </tr>
          </thead>
          <tbody>
            {active.map(item => (
              <tr key={item.id} className="border-b border-border last:border-0 hover:bg-bg-hover">
                <td className="px-4 py-2">
                  <Link to={`/wines/${item.wine_id}`} className="text-accent hover:underline">
                    {item.wine_producer} {item.wine_name}
                  </Link>
                </td>
                <td className="px-4 py-2 tabular-nums text-text-secondary">{item.wine_vintage || '-'}</td>
                <td className="px-4 py-2 text-text-secondary">{item.notes || '-'}</td>
                <td className="px-4 py-2 text-xs text-text-secondary tabular-nums">
                  {new Date(item.wishlisted_at).toLocaleDateString('en-GB')}
                </td>
                <td className="px-4 py-2 text-center">
                  <button
                    onClick={() => updateWishlist.mutate({ id: item.id, data: { acquired: true } })}
                    className="text-xs text-success hover:underline mr-2"
                  >
                    Acquired
                  </button>
                  <button
                    onClick={() => deleteWishlist.mutate(item.id)}
                    className="text-xs text-text-secondary hover:text-accent"
                  >
                    Remove
                  </button>
                </td>
              </tr>
            ))}
            {active.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-text-secondary">
                  No wines on wishlist
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {acquired.length > 0 && (
        <>
          <h3 className="text-sm font-medium text-text-secondary mt-6">Acquired</h3>
          <div className="bg-bg-card border border-border rounded-lg overflow-x-auto opacity-60">
            <table className="w-full text-sm">
              <tbody>
                {acquired.map(item => (
                  <tr key={item.id} className="border-b border-border last:border-0">
                    <td className="px-4 py-2 line-through">
                      {item.wine_producer} {item.wine_name}
                      {item.wine_vintage ? ` ${item.wine_vintage}` : ''}
                    </td>
                    <td className="px-4 py-2 text-text-secondary">{item.notes || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  )
}
