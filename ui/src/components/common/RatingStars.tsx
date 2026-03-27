interface Props {
  rating: number | null
  size?: 'sm' | 'md'
}

export default function RatingStars({ rating, size = 'md' }: Props) {
  if (rating === null || rating === undefined) return <span className="text-text-secondary text-xs">-</span>

  const full = Math.floor(rating)
  const half = rating - full >= 0.25
  const textSize = size === 'sm' ? 'text-xs' : 'text-sm'

  return (
    <span className={`${textSize} text-accent tabular-nums`} title={`${rating.toFixed(1)}/5`}>
      {'★'.repeat(full)}{half ? '½' : ''}{'☆'.repeat(5 - full - (half ? 1 : 0))}
    </span>
  )
}
