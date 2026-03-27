import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useWine, useWineLog, useAddLog, useUpdateWine } from '../hooks/useWines.ts'
import RatingStars from '../components/common/RatingStars.tsx'
import LoadingSpinner from '../components/common/LoadingSpinner.tsx'

export default function WineDetail() {
  const { id } = useParams<{ id: string }>()
  const wineId = Number(id)
  const { data: wine, isLoading } = useWine(wineId)
  const { data: log } = useWineLog(wineId)
  const addLog = useAddLog()
  const updateWine = useUpdateWine()
  const [showAddLog, setShowAddLog] = useState(false)
  const [editing, setEditing] = useState(false)
  const [logForm, setLogForm] = useState({ rating: '', review: '', personal_note: '', location: '' })
  const [editForm, setEditForm] = useState<Record<string, string>>({})

  if (isLoading || !wine) return <LoadingSpinner />

  const handleAddLog = () => {
    const data: Record<string, unknown> = {}
    if (logForm.rating) data.rating = parseFloat(logForm.rating)
    if (logForm.review) data.review = logForm.review
    if (logForm.personal_note) data.personal_note = logForm.personal_note
    if (logForm.location) data.location = logForm.location
    addLog.mutate({ wineId, data }, {
      onSuccess: () => {
        setShowAddLog(false)
        setLogForm({ rating: '', review: '', personal_note: '', location: '' })
      },
    })
  }

  const handleSaveEdit = () => {
    const data: Record<string, unknown> = {}
    for (const [k, v] of Object.entries(editForm)) {
      if (v !== '') data[k] = k === 'vintage' ? parseInt(v) : k === 'abv' ? parseFloat(v) : v
    }
    if (Object.keys(data).length > 0) {
      updateWine.mutate({ id: wineId, data })
    }
    setEditing(false)
  }

  const startEdit = () => {
    setEditForm({
      producer: wine.producer,
      name: wine.name,
      vintage: wine.vintage?.toString() ?? '',
      region: wine.region ?? '',
      country: wine.country ?? '',
      wine_type: wine.wine_type ?? '',
      grape_variety: wine.grape_variety ?? '',
      abv: wine.abv?.toString() ?? '',
    })
    setEditing(true)
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="bg-bg-card border border-border rounded-lg p-6">
        <div className="flex items-start justify-between">
          <div>
            {editing ? (
              <div className="space-y-2">
                {['producer', 'name', 'vintage', 'region', 'country', 'wine_type', 'grape_variety', 'abv'].map(field => (
                  <div key={field} className="flex gap-2 items-center">
                    <label className="text-xs text-text-secondary w-24">{field}</label>
                    <input
                      value={editForm[field] ?? ''}
                      onChange={e => setEditForm({ ...editForm, [field]: e.target.value })}
                      className="px-2 py-1 text-sm border border-border rounded bg-bg-secondary w-64"
                    />
                  </div>
                ))}
                <div className="flex gap-2 mt-2">
                  <button onClick={handleSaveEdit} className="px-3 py-1 text-sm bg-accent text-white rounded hover:bg-accent-hover">Save</button>
                  <button onClick={() => setEditing(false)} className="px-3 py-1 text-sm border border-border rounded hover:bg-bg-hover">Cancel</button>
                </div>
              </div>
            ) : (
              <>
                <h2 className="text-xl font-semibold">{wine.producer}</h2>
                <h3 className="text-lg text-text-secondary">
                  {wine.name}{wine.vintage ? ` ${wine.vintage}` : ''}
                </h3>
                <div className="flex gap-4 mt-2 text-sm text-text-secondary">
                  {wine.country && <span>{wine.region ? `${wine.region}, ` : ''}{wine.country}</span>}
                  {wine.wine_type && <span>{wine.wine_type}</span>}
                  {wine.grape_variety && <span>{wine.grape_variety}</span>}
                  {wine.abv && <span>{wine.abv}%</span>}
                </div>
                {wine.drinking_window && (
                  <div className="text-xs text-text-secondary mt-1">Drinking window: {wine.drinking_window}</div>
                )}
                <button onClick={startEdit} className="mt-2 text-xs text-accent hover:underline">Edit</button>
              </>
            )}
          </div>
          <div className="text-right space-y-1">
            <RatingStars rating={wine.avg_personal_rating} />
            <div className="text-xs text-text-secondary">{wine.tasting_count} tasting{wine.tasting_count !== 1 ? 's' : ''}</div>
            {wine.vivino_avg_rating && (
              <div className="text-xs text-text-secondary">
                Vivino: {wine.vivino_avg_rating}/5
                {wine.vivino_url && (
                  <a href={wine.vivino_url} target="_blank" rel="noreferrer" className="text-accent ml-1 hover:underline">view</a>
                )}
              </div>
            )}
          </div>
        </div>

        <div className="flex gap-3 mt-4">
          {wine.cellar_quantity > 0 && (
            <span className="inline-flex items-center px-2 py-0.5 text-xs rounded bg-success/15 text-success">
              {wine.cellar_quantity} in cellar{wine.cellar_location ? ` (${wine.cellar_location})` : ''}
            </span>
          )}
          {wine.is_wishlisted && (
            <span className="inline-flex items-center px-2 py-0.5 text-xs rounded bg-warning/15 text-warning">
              Wishlisted
            </span>
          )}
        </div>
      </div>

      <div className="bg-bg-card border border-border rounded-lg p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-medium text-text-secondary">Tasting History</h3>
          <button
            onClick={() => setShowAddLog(!showAddLog)}
            className="px-3 py-1 text-sm bg-accent text-white rounded hover:bg-accent-hover"
          >
            Add Tasting
          </button>
        </div>

        {showAddLog && (
          <div className="border border-border rounded-md p-4 mb-4 space-y-3">
            <div className="flex gap-4">
              <div>
                <label className="text-xs text-text-secondary">Rating (1-5)</label>
                <input
                  type="number"
                  min="1"
                  max="5"
                  step="0.5"
                  value={logForm.rating}
                  onChange={e => setLogForm({ ...logForm, rating: e.target.value })}
                  className="block w-20 px-2 py-1 text-sm border border-border rounded bg-bg-secondary"
                />
              </div>
              <div className="flex-1">
                <label className="text-xs text-text-secondary">Location</label>
                <input
                  value={logForm.location}
                  onChange={e => setLogForm({ ...logForm, location: e.target.value })}
                  className="block w-full px-2 py-1 text-sm border border-border rounded bg-bg-secondary"
                />
              </div>
            </div>
            <div>
              <label className="text-xs text-text-secondary">Review</label>
              <textarea
                value={logForm.review}
                onChange={e => setLogForm({ ...logForm, review: e.target.value })}
                rows={2}
                className="block w-full px-2 py-1 text-sm border border-border rounded bg-bg-secondary"
              />
            </div>
            <div>
              <label className="text-xs text-text-secondary">Personal Note</label>
              <textarea
                value={logForm.personal_note}
                onChange={e => setLogForm({ ...logForm, personal_note: e.target.value })}
                rows={2}
                className="block w-full px-2 py-1 text-sm border border-border rounded bg-bg-secondary"
              />
            </div>
            <div className="flex gap-2">
              <button onClick={handleAddLog} className="px-3 py-1 text-sm bg-accent text-white rounded hover:bg-accent-hover">Save</button>
              <button onClick={() => setShowAddLog(false)} className="px-3 py-1 text-sm border border-border rounded hover:bg-bg-hover">Cancel</button>
            </div>
          </div>
        )}

        <div className="space-y-3">
          {log?.map(entry => (
            <div key={entry.id} className="flex gap-4 py-3 border-b border-border last:border-0">
              {entry.label_image_filename && (
                <a href={`/api/v1/labels/${entry.label_image_filename}`} target="_blank" rel="noreferrer">
                  <img
                    src={`/api/v1/labels/${entry.label_image_filename}`}
                    alt="Label"
                    className="w-12 h-16 object-cover rounded border border-border"
                  />
                </a>
              )}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <RatingStars rating={entry.rating} size="sm" />
                  <span className="text-xs text-text-secondary">
                    {new Date(entry.logged_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })}
                  </span>
                  <span className="text-xs text-text-secondary px-1.5 py-0.5 rounded bg-bg-primary">{entry.source}</span>
                </div>
                {entry.review && <p className="text-sm mt-1">{entry.review}</p>}
                {entry.personal_note && <p className="text-sm text-text-secondary mt-1 italic">{entry.personal_note}</p>}
                {entry.location && <p className="text-xs text-text-secondary mt-1">{entry.location}</p>}
              </div>
            </div>
          ))}
          {(!log || log.length === 0) && (
            <div className="text-sm text-text-secondary py-4 text-center">No tastings recorded yet</div>
          )}
        </div>
      </div>
    </div>
  )
}
