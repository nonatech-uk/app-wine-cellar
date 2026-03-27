import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useWines } from '../hooks/useWines.ts'
import RatingStars from '../components/common/RatingStars.tsx'
import LoadingSpinner from '../components/common/LoadingSpinner.tsx'

export default function Wines() {
  const [q, setQ] = useState('')
  const [country, setCountry] = useState('')
  const [wineType, setWineType] = useState('')
  const [sort, setSort] = useState('name')
  const [offset, setOffset] = useState(0)
  const limit = 50

  const { data, isLoading } = useWines({ q: q || undefined, country: country || undefined, wine_type: wineType || undefined, sort, limit, offset })

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold">Wines</h2>

      <div className="flex gap-3 flex-wrap">
        <input
          type="text"
          placeholder="Search producer or wine..."
          value={q}
          onChange={e => { setQ(e.target.value); setOffset(0) }}
          className="px-3 py-1.5 text-sm border border-border rounded-md bg-bg-secondary focus:outline-none focus:ring-1 focus:ring-accent w-64"
        />
        <select
          value={country}
          onChange={e => { setCountry(e.target.value); setOffset(0) }}
          className="px-3 py-1.5 text-sm border border-border rounded-md bg-bg-secondary"
        >
          <option value="">All countries</option>
          {['France', 'Italy', 'Switzerland', 'Spain', 'United States', 'Argentina', 'Australia'].map(c => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
        <select
          value={wineType}
          onChange={e => { setWineType(e.target.value); setOffset(0) }}
          className="px-3 py-1.5 text-sm border border-border rounded-md bg-bg-secondary"
        >
          <option value="">All types</option>
          {['Red Wine', 'White Wine', 'Rosé Wine', 'Sparkling', 'Dessert Wine'].map(t => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
        <select
          value={sort}
          onChange={e => { setSort(e.target.value); setOffset(0) }}
          className="px-3 py-1.5 text-sm border border-border rounded-md bg-bg-secondary"
        >
          <option value="name">Name</option>
          <option value="rating">Rating</option>
          <option value="recent">Recent</option>
          <option value="country">Country</option>
        </select>
      </div>

      {data && (
        <div className="text-xs text-text-secondary">{data.total} wines</div>
      )}

      {isLoading ? (
        <LoadingSpinner />
      ) : (
        <div className="bg-bg-card border border-border rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-bg-primary">
                <th className="text-left px-4 py-2 font-medium text-text-secondary">Producer</th>
                <th className="text-left px-4 py-2 font-medium text-text-secondary">Wine</th>
                <th className="text-left px-4 py-2 font-medium text-text-secondary w-16">Year</th>
                <th className="text-left px-4 py-2 font-medium text-text-secondary">Country</th>
                <th className="text-left px-4 py-2 font-medium text-text-secondary">Type</th>
                <th className="text-left px-4 py-2 font-medium text-text-secondary w-24">Rating</th>
                <th className="text-left px-4 py-2 font-medium text-text-secondary w-20">Tastings</th>
              </tr>
            </thead>
            <tbody>
              {data?.items.map(wine => (
                <tr key={wine.id} className="border-b border-border last:border-0 hover:bg-bg-hover transition-colors">
                  <td className="px-4 py-2">
                    <Link to={`/wines/${wine.id}`} className="text-accent hover:underline">
                      {wine.producer}
                    </Link>
                  </td>
                  <td className="px-4 py-2">
                    <Link to={`/wines/${wine.id}`} className="hover:text-accent">
                      {wine.name}
                    </Link>
                  </td>
                  <td className="px-4 py-2 tabular-nums text-text-secondary">{wine.vintage || '-'}</td>
                  <td className="px-4 py-2 text-text-secondary">{wine.country || '-'}</td>
                  <td className="px-4 py-2 text-text-secondary">{wine.wine_type || '-'}</td>
                  <td className="px-4 py-2"><RatingStars rating={wine.avg_personal_rating} size="sm" /></td>
                  <td className="px-4 py-2 tabular-nums text-text-secondary">{wine.tasting_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {data && (data.has_more || offset > 0) && (
        <div className="flex gap-2 justify-center">
          <button
            onClick={() => setOffset(Math.max(0, offset - limit))}
            disabled={offset === 0}
            className="px-3 py-1 text-sm rounded border border-border disabled:opacity-30 hover:bg-bg-hover"
          >
            Previous
          </button>
          <button
            onClick={() => setOffset(offset + limit)}
            disabled={!data.has_more}
            className="px-3 py-1 text-sm rounded border border-border disabled:opacity-30 hover:bg-bg-hover"
          >
            Next
          </button>
        </div>
      )}
    </div>
  )
}
