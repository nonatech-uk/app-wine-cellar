import { useMemo } from 'react'
import { Link } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Tooltip } from 'recharts'
import { useOverview, useByCountry, useTimeline, useRecentLog } from '../hooks/useWines.ts'
import StatCard from '../components/common/StatCard.tsx'
import RatingStars from '../components/common/RatingStars.tsx'
import LoadingSpinner from '../components/common/LoadingSpinner.tsx'

export default function Dashboard() {
  const { data: overview, isLoading } = useOverview()
  const { data: countries } = useByCountry()
  const { data: timeline } = useTimeline()
  const { data: recent } = useRecentLog(10)

  const chartData = useMemo(() => {
    if (!timeline) return []
    return timeline.map(t => ({
      month: t.month.slice(5),
      count: t.count,
    }))
  }, [timeline])

  const topCountries = useMemo(() => {
    if (!countries) return []
    return countries.slice(0, 8)
  }, [countries])

  if (isLoading) return <LoadingSpinner />

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold">Dashboard</h2>

      {overview && (
        <div className="grid grid-cols-3 lg:grid-cols-6 gap-4">
          <StatCard label="Total Wines" value={overview.total_wines} />
          <StatCard label="Countries" value={overview.total_countries} />
          <StatCard label="Tastings" value={overview.total_tastings} />
          <StatCard label="Avg Rating" value={overview.avg_rating ? `${overview.avg_rating}/5` : '-'} />
          <StatCard label="Cellar Bottles" value={overview.cellar_bottles} />
          <StatCard label="This Month" value={overview.tastings_this_month} />
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {chartData.length > 0 && (
          <div className="bg-bg-card border border-border rounded-lg p-5">
            <h3 className="text-sm font-medium text-text-secondary mb-4">Tastings per Month</h3>
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e4e8" />
                <XAxis dataKey="month" tick={{ fill: '#6b7280', fontSize: 11 }} />
                <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="count" fill="#7c2d42" radius={[2, 2, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {topCountries.length > 0 && (
          <div className="bg-bg-card border border-border rounded-lg p-5">
            <h3 className="text-sm font-medium text-text-secondary mb-4">Top Countries</h3>
            <div className="space-y-2">
              {topCountries.map(c => (
                <div key={c.country} className="flex items-center gap-3">
                  <div className="w-20 text-sm truncate">{c.country}</div>
                  <div className="flex-1 bg-bg-primary rounded h-5 overflow-hidden">
                    <div
                      className="bg-accent/20 h-full rounded"
                      style={{ width: `${(c.count / (topCountries[0]?.count || 1)) * 100}%` }}
                    />
                  </div>
                  <div className="text-sm tabular-nums text-text-secondary w-8 text-right">{c.count}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {recent && recent.length > 0 && (
        <div className="bg-bg-card border border-border rounded-lg p-5">
          <h3 className="text-sm font-medium text-text-secondary mb-4">Recent Tastings</h3>
          <div className="space-y-2">
            {recent.map(entry => (
              <Link
                key={entry.id}
                to={`/wines/${entry.wine_id}`}
                className="flex items-center gap-4 px-3 py-2 rounded-md hover:bg-bg-hover transition-colors"
              >
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium truncate">
                    {entry.wine_producer} {entry.wine_name}
                    {entry.wine_vintage ? ` ${entry.wine_vintage}` : ''}
                  </div>
                  {entry.location && (
                    <div className="text-xs text-text-secondary truncate">{entry.location}</div>
                  )}
                </div>
                <RatingStars rating={entry.rating} size="sm" />
                <div className="text-xs text-text-secondary tabular-nums w-20 text-right">
                  {new Date(entry.logged_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: '2-digit' })}
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
