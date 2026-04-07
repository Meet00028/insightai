"""
# Architect: Meet Kumar
# InsightAI - Dashboard Endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.core.database import get_db
from app.models.user import User
from app.models.dataset import Dataset, DatasetStatus
from app.models.analysis_session import AnalysisSession
from app.api.auth import get_current_active_user
from app.api.schemas import DashboardStats, DatasetResponse, AnalysisResponse

router = APIRouter()


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get dashboard statistics for the current user."""
    
    # Get total datasets
    datasets_result = await db.execute(
        select(func.count()).select_from(
            select(Dataset).where(Dataset.user_id == current_user.id).subquery()
        )
    )
    total_datasets = datasets_result.scalar()
    
    # Get total analyses
    analyses_result = await db.execute(
        select(func.count()).select_from(
            select(AnalysisSession).where(AnalysisSession.user_id == current_user.id).subquery()
        )
    )
    total_analyses = analyses_result.scalar()
    
    # Get average health score
    health_result = await db.execute(
        select(func.avg(Dataset.data_health_score)).where(
            Dataset.user_id == current_user.id,
            Dataset.data_health_score.isnot(None)
        )
    )
    avg_health = health_result.scalar()
    
    # Get recent datasets
    recent_datasets_result = await db.execute(
        select(Dataset)
        .where(Dataset.user_id == current_user.id)
        .order_by(desc(Dataset.created_at))
        .limit(5)
    )
    recent_datasets = recent_datasets_result.scalars().all()
    
    # Get recent analyses
    recent_analyses_result = await db.execute(
        select(AnalysisSession)
        .where(AnalysisSession.user_id == current_user.id)
        .order_by(desc(AnalysisSession.created_at))
        .limit(5)
    )
    recent_analyses = recent_analyses_result.scalars().all()
    
    # Format storage used
    storage_bytes = current_user.storage_used_bytes or 0
    if storage_bytes < 1024:
        storage_formatted = f"{storage_bytes} B"
    elif storage_bytes < 1024 * 1024:
        storage_formatted = f"{storage_bytes / 1024:.1f} KB"
    elif storage_bytes < 1024 * 1024 * 1024:
        storage_formatted = f"{storage_bytes / (1024 * 1024):.1f} MB"
    else:
        storage_formatted = f"{storage_bytes / (1024 * 1024 * 1024):.2f} GB"
    
    return DashboardStats(
        total_datasets=total_datasets,
        total_analyses=total_analyses,
        storage_used_bytes=storage_bytes,
        storage_used_formatted=storage_formatted,
        recent_datasets=[DatasetResponse.model_validate(d) for d in recent_datasets],
        recent_analyses=[AnalysisResponse.model_validate(a) for a in recent_analyses],
        data_health_average=round(avg_health, 2) if avg_health else None
    )


@router.get("/activity")
async def get_recent_activity(
    limit: int = 10,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get recent user activity."""
    
    # Get recent datasets
    datasets_result = await db.execute(
        select(Dataset)
        .where(Dataset.user_id == current_user.id)
        .order_by(desc(Dataset.created_at))
        .limit(limit)
    )
    datasets = datasets_result.scalars().all()
    
    # Get recent analyses
    analyses_result = await db.execute(
        select(AnalysisSession)
        .where(AnalysisSession.user_id == current_user.id)
        .order_by(desc(AnalysisSession.created_at))
        .limit(limit)
    )
    analyses = analyses_result.scalars().all()
    
    # Combine and sort by date
    activities = []
    
    for dataset in datasets:
        activities.append({
            "type": "dataset_uploaded",
            "title": f"Uploaded dataset: {dataset.name}",
            "timestamp": dataset.created_at.isoformat(),
            "status": dataset.status.value,
            "id": str(dataset.id),
        })
    
    for analysis in analyses:
        activities.append({
            "type": "analysis_completed" if analysis.status.value == "completed" else "analysis_started",
            "title": f"Analysis: {analysis.query or 'Exploratory Analysis'}",
            "timestamp": analysis.created_at.isoformat(),
            "status": analysis.status.value,
            "id": str(analysis.id),
        })
    
    # Sort by timestamp (newest first)
    activities.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return {"activities": activities[:limit]}


@router.get("/storage")
async def get_storage_usage(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed storage usage information."""
    
    # Get storage by dataset status
    status_result = await db.execute(
        select(Dataset.status, func.count(), func.sum(Dataset.file_size))
        .where(Dataset.user_id == current_user.id)
        .group_by(Dataset.status)
    )
    by_status = [
        {
            "status": status.value,
            "count": count,
            "size_bytes": size or 0,
            "size_formatted": _format_size(size or 0)
        }
        for status, count, size in status_result.all()
    ]
    
    # Get largest datasets
    largest_result = await db.execute(
        select(Dataset)
        .where(Dataset.user_id == current_user.id)
        .order_by(desc(Dataset.file_size))
        .limit(10)
    )
    largest_datasets = largest_result.scalars().all()
    
    # Subscription limits (example values)
    tier_limits = {
        "free": 100 * 1024 * 1024,  # 100 MB
        "pro": 10 * 1024 * 1024 * 1024,  # 10 GB
        "enterprise": 100 * 1024 * 1024 * 1024,  # 100 GB
    }
    
    tier = current_user.subscription_tier.value
    limit = tier_limits.get(tier, tier_limits["free"])
    used = current_user.storage_used_bytes or 0
    
    return {
        "total_used_bytes": used,
        "total_used_formatted": _format_size(used),
        "limit_bytes": limit,
        "limit_formatted": _format_size(limit),
        "usage_percentage": round((used / limit) * 100, 2) if limit > 0 else 0,
        "by_status": by_status,
        "largest_datasets": [
            {
                "id": str(d.id),
                "name": d.name,
                "size_bytes": d.file_size,
                "size_formatted": _format_size(d.file_size)
            }
            for d in largest_datasets
        ]
    }


def _format_size(size_bytes: int) -> str:
    """Format bytes to human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
