"""Anonymous location endpoints for real-time user map"""

from datetime import datetime, timedelta, UTC
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_current_user, get_async_session
from db.models import User, AnonymousLocation
from services.geocoding import GeocodingService
from core.config import settings

router = APIRouter(prefix="/locations", tags=["locations"])

# Global geocoding service cache
_geocoding_service = None


def get_geocoding_service() -> GeocodingService | None:
    """Get geocoding service instance (returns None if not configured)"""
    global _geocoding_service
    if _geocoding_service is None and settings.GOOGLE_MAPS_API_KEY != "your-google-maps-api-key-here":
        try:
            _geocoding_service = GeocodingService(google_api_key=settings.GOOGLE_MAPS_API_KEY)
        except Exception:
            pass  # Geocoding is optional enhancement
    return _geocoding_service


class AnonymousLocationResponse(BaseModel):
    """Anonymous location for map display"""
    location_id: UUID
    latitude: float
    longitude: float
    area_name: str | None = None
    last_updated: datetime

    class Config:
        from_attributes = True


@router.get("/anonymous/active", response_model=List[AnonymousLocationResponse])
async def get_active_anonymous_locations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get all active anonymous locations (updated within last 15 minutes)

    Returns locations with precise coordinates for clustering.
    Optionally includes area names via reverse geocoding if Google Maps API is configured.

    **Privacy**: No user identification - completely anonymous.
    """
    # Calculate 15-minute expiration threshold
    expiration_threshold = datetime.now(UTC) - timedelta(minutes=15)

    # Query active locations
    result = await db.execute(
        select(AnonymousLocation)
        .where(AnonymousLocation.last_updated >= expiration_threshold)
        .order_by(AnonymousLocation.last_updated.desc())
    )
    locations = result.scalars().all()

    # Build response with optional area names
    geocoding_service = get_geocoding_service()
    response_locations = []

    for loc in locations:
        area_name = None

        # Optionally add area name via reverse geocoding
        if geocoding_service:
            try:
                reverse_result = geocoding_service.reverse_geocode(loc.latitude, loc.longitude)
                if reverse_result and reverse_result.address:
                    # Format: "Wynwood, Miami" or just "Miami"
                    parts = []
                    if reverse_result.address.city:
                        # Try to get neighborhood/area if available
                        formatted = reverse_result.address.formatted_address
                        # Extract first part before comma (usually neighborhood or specific area)
                        first_part = formatted.split(',')[0].strip() if ',' in formatted else None
                        if first_part and first_part != reverse_result.address.city:
                            parts.append(first_part)
                        else:
                            parts.append(reverse_result.address.city)
                    area_name = ", ".join(parts) if parts else None
            except Exception:
                pass  # Continue without area name if geocoding fails

        response_locations.append(
            AnonymousLocationResponse(
                location_id=loc.location_id,
                latitude=loc.latitude,
                longitude=loc.longitude,
                area_name=area_name,
                last_updated=loc.last_updated
            )
        )

    return response_locations


@router.delete("/anonymous/cleanup")
async def cleanup_expired_locations(
    db: AsyncSession = Depends(get_async_session)
):
    """
    Cleanup endpoint for expired anonymous locations (older than 15 minutes)

    **Internal use**: Called by background job or manually for maintenance.
    Does NOT require authentication - can be triggered by scheduler.
    """
    expiration_threshold = datetime.now(UTC) - timedelta(minutes=15)

    result = await db.execute(
        delete(AnonymousLocation)
        .where(AnonymousLocation.last_updated < expiration_threshold)
    )
    await db.commit()

    deleted_count = result.rowcount

    return {
        "deleted_count": deleted_count,
        "expiration_threshold": expiration_threshold.isoformat()
    }


# NOTE: Activity clusters endpoint has been archived - see archived/activity_clustering.py
# The client app is no longer using the live feed / activity clustering functionality
# Archived endpoint: GET /locations/activity-clusters
