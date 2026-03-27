from fastapi import APIRouter, Depends

from src.api.deps import CurrentUser, get_conn, get_current_user
from src.api.models import CountryStat, OverviewStats, TimelinePoint

router = APIRouter()


@router.get("/stats/overview", response_model=OverviewStats)
def overview(
    conn=Depends(get_conn),
    _user: CurrentUser = Depends(get_current_user),
):
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM wine")
    total_wines = cur.fetchone()[0]

    cur.execute("SELECT count(DISTINCT country) FROM wine WHERE country IS NOT NULL")
    total_countries = cur.fetchone()[0]

    cur.execute("SELECT count(*) FROM wine_log")
    total_tastings = cur.fetchone()[0]

    cur.execute("SELECT avg(rating) FROM wine_log WHERE rating IS NOT NULL")
    avg_rating = cur.fetchone()[0]

    cur.execute("SELECT COALESCE(sum(quantity), 0) FROM wine_cellar WHERE quantity > 0")
    cellar_bottles = cur.fetchone()[0]

    cur.execute("""
        SELECT count(*) FROM wine_log
        WHERE logged_at >= date_trunc('month', now())
    """)
    tastings_this_month = cur.fetchone()[0]

    return OverviewStats(
        total_wines=total_wines,
        total_countries=total_countries,
        total_tastings=total_tastings,
        avg_rating=round(float(avg_rating), 2) if avg_rating else None,
        cellar_bottles=cellar_bottles,
        tastings_this_month=tastings_this_month,
    )


@router.get("/stats/by-country", response_model=list[CountryStat])
def by_country(
    conn=Depends(get_conn),
    _user: CurrentUser = Depends(get_current_user),
):
    cur = conn.cursor()
    cur.execute("""
        SELECT w.country, count(*) AS cnt,
               round(avg(w.vivino_avg_rating)::numeric, 2) AS avg_rating
        FROM wine w
        WHERE w.country IS NOT NULL
        GROUP BY w.country
        ORDER BY cnt DESC
    """)
    return [
        CountryStat(country=r[0], count=r[1], avg_rating=float(r[2]) if r[2] else None)
        for r in cur.fetchall()
    ]


@router.get("/stats/timeline", response_model=list[TimelinePoint])
def timeline(
    conn=Depends(get_conn),
    _user: CurrentUser = Depends(get_current_user),
):
    cur = conn.cursor()
    cur.execute("""
        SELECT to_char(logged_at, 'YYYY-MM') AS month, count(*) AS cnt
        FROM wine_log
        WHERE logged_at >= now() - interval '24 months'
        GROUP BY month
        ORDER BY month
    """)
    return [TimelinePoint(month=r[0], count=r[1]) for r in cur.fetchall()]
