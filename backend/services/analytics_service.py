import logging
from typing import Dict, Any, List
from backend.models.shipment import Shipment
from backend.models.tracking_event import TrackingEvent
from backend.extensions import db
from sqlalchemy import func
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)

class AnalyticsService:
    @staticmethod
    def get_overview_stats(user_id: int) -> Dict[str, Any]:
        try:
            base_query = Shipment.query.filter_by(user_id=user_id, is_archived=False)
            total = base_query.count()
            in_transit = base_query.filter_by(status='IN_TRANSIT').count()
            delivered = base_query.filter_by(status='DELIVERED').count()
            delayed = base_query.filter(Shipment.status.in_(['DELAYED', 'EXCEPTION'])).count()
            
            delivery_rate = 0.0
            if total > 0:
                delivery_rate = round((delivered / total) * 100, 1)
                
            # Calculate average time in days using python to remain DB agnostic
            delivered_shipments = base_query.filter_by(status='DELIVERED').all()
            total_days = 0
            valid_times = 0
            for s in delivered_shipments:
                if s.created_at and s.updated_at:
                    days = (s.updated_at - s.created_at).total_seconds() / (24 * 3600)
                    if days > 0:
                        total_days += days
                        valid_times += 1
                        
            avg_time = round(total_days / valid_times, 1) if valid_times > 0 else 0
                
            return {
                'total': total,
                'in_transit': in_transit,
                'delivered': delivered,
                'delayed': delayed,
                'delivery_rate': delivery_rate,
                'avg_time': avg_time
            }
        except Exception as e:
            logger.error(f"Error getting overview stats: {e}")
            return {'total': 0, 'in_transit': 0, 'delivered': 0, 'delayed': 0, 'delivery_rate': 0.0, 'avg_time': 0}

    @staticmethod
    def get_shipments_by_status(user_id: int) -> List[Dict[str, Any]]:
        try:
            results = db.session.query(Shipment.status, func.count(Shipment.id)).filter_by(user_id=user_id, is_archived=False).group_by(Shipment.status).all()
            return [{'status': r[0], 'count': r[1]} for r in results]
        except Exception as e:
            logger.error(f"Error getting shipments by status: {e}")
            return []

    @staticmethod
    def get_common_locations(user_id: int) -> List[Dict[str, Any]]:
        try:
            results = db.session.query(TrackingEvent.location, func.count(TrackingEvent.id)).join(Shipment).filter(Shipment.user_id == user_id).group_by(TrackingEvent.location).order_by(func.count(TrackingEvent.id).desc()).limit(10).all()
            return [{'location': r[0] if r[0] else 'Unknown', 'count': r[1]} for r in results]
        except Exception as e:
            logger.error(f"Error getting common locations: {e}")
            return []

    @staticmethod
    def get_shipments_over_time(user_id: int, months: int = 6) -> List[Dict[str, Any]]:
        """Get shipment count grouped by month for the last N months."""
        try:
            from sqlalchemy import extract
            from datetime import datetime, timedelta
            
            cutoff = datetime.utcnow() - timedelta(days=months * 30)
            
            results = db.session.query(
                extract('year', Shipment.created_at).label('year'),
                extract('month', Shipment.created_at).label('month'),
                func.count(Shipment.id).label('count')
            ).filter(
                Shipment.user_id == user_id,
                Shipment.is_archived == False,
                Shipment.created_at >= cutoff
            ).group_by('year', 'month').order_by('year', 'month').all()
            
            # Build continuous timeline
            month_data = defaultdict(int)
            for r in results:
                key = f"{int(r.year)}-{int(r.month):02d}"
                month_data[key] = r.count
            
            # Fill in missing months with 0
            result_list = []
            current = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            for i in range(months):
                month_start = current - timedelta(days=i * 30)
                # Approximate month boundaries
                year = month_start.year
                month = month_start.month
                key = f"{year}-{month:02d}"
                label = month_start.strftime("%b %Y")
                result_list.append({
                    'period': label,
                    'count': month_data.get(key, 0)
                })
            
            return list(reversed(result_list))
        except Exception as e:
            logger.error(f"Error getting shipments over time: {e}")
            return []

    @staticmethod
    def get_delivery_time_distribution(user_id: int) -> List[Dict[str, Any]]:
        """Get histogram data for delivery times (in days)."""
        try:
            delivered_shipments = Shipment.query.filter_by(
                user_id=user_id, 
                is_archived=False, 
                status='DELIVERED'
            ).all()
            
            if not delivered_shipments:
                return []
            
            delivery_times = []
            for s in delivered_shipments:
                if s.created_at and s.updated_at:
                    days = (s.updated_at - s.created_at).total_seconds() / (24 * 3600)
                    if days > 0:
                        delivery_times.append(round(days, 1))
            
            if not delivery_times:
                return []
            
            # Create histogram bins
            max_days = max(delivery_times)
            min_days = min(delivery_times)
            
            # Use 1-day bins up to max, or group into ranges
            bin_size = 1 if max_days <= 14 else (2 if max_days <= 30 else 5)
            bins = defaultdict(int)
            
            for d in delivery_times:
                bin_start = int(d // bin_size) * bin_size
                bin_label = f"{bin_start}-{bin_start + bin_size - 1} days"
                if bin_size > 1:
                    bin_label = f"{bin_start}-{bin_start + bin_size - 1} days"
                else:
                    bin_label = f"{bin_start} day" if bin_start == 1 else f"{bin_start} days"
                bins[bin_label] += 1
            
            # Sort by bin start
            sorted_bins = sorted(bins.items(), key=lambda x: int(x[0].split('-')[0].split()[0]) if '-' in x[0] else int(x[0].split()[0]))
            
            return [{'range': k, 'count': v} for k, v in sorted_bins]
        except Exception as e:
            logger.error(f"Error getting delivery time distribution: {e}")
            return []

    @staticmethod
    def get_avg_delivery_time_by_carrier(user_id: int) -> List[Dict[str, Any]]:
        """Get average delivery time grouped by carrier."""
        try:
            delivered_shipments = Shipment.query.filter_by(
                user_id=user_id, 
                is_archived=False, 
                status='DELIVERED'
            ).all()
            
            carrier_times = defaultdict(list)
            for s in delivered_shipments:
                if s.created_at and s.updated_at:
                    days = (s.updated_at - s.created_at).total_seconds() / (24 * 3600)
                    if days > 0:
                        carrier_times[s.carrier].append(days)
            
            result = []
            for carrier, times in carrier_times.items():
                if times:
                    avg = round(sum(times) / len(times), 1)
                    result.append({
                        'carrier': carrier,
                        'avg_days': avg,
                        'count': len(times)
                    })
            
            return sorted(result, key=lambda x: x['avg_days'])
        except Exception as e:
            logger.error(f"Error getting avg delivery time by carrier: {e}")
            return []

    @staticmethod
    def get_avg_delivery_time_by_location(user_id: int, min_count: int = 3) -> List[Dict[str, Any]]:
        """Get average delivery time grouped by destination/origin location."""
        try:
            delivered_shipments = Shipment.query.filter_by(
                user_id=user_id, 
                is_archived=False, 
                status='DELIVERED'
            ).all()
            
            location_times = defaultdict(list)
            for s in delivered_shipments:
                if s.created_at and s.updated_at and s.destination:
                    days = (s.updated_at - s.created_at).total_seconds() / (24 * 3600)
                    if days > 0:
                        location_times[s.destination].append(days)
            
            result = []
            for location, times in location_times.items():
                if len(times) >= min_count:
                    avg = round(sum(times) / len(times), 1)
                    result.append({
                        'location': location,
                        'avg_days': avg,
                        'count': len(times)
                    })
            
            return sorted(result, key=lambda x: x['avg_days'])
        except Exception as e:
            logger.error(f"Error getting avg delivery time by location: {e}")
            return []

    @staticmethod
    def get_stale_shipments(user_id: int, days_threshold: int = 7) -> List[Dict[str, Any]]:
        """Get shipments that haven't been updated in N days."""
        try:
            from datetime import datetime, timedelta
            cutoff = datetime.utcnow() - timedelta(days=days_threshold)
            
            shipments = Shipment.query.filter(
                Shipment.user_id == user_id,
                Shipment.is_archived == False,
                Shipment.status.notin_(['DELIVERED', 'EXCEPTION']),
                Shipment.last_updated < cutoff
            ).order_by(Shipment.last_updated.asc()).all()
            
            return [s.to_dict() for s in shipments]
        except Exception as e:
            logger.error(f"Error getting stale shipments: {e}")
            return []

    @staticmethod
    def get_recent_activity(user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent tracking activity across all shipments."""
        try:
            events = db.session.query(TrackingEvent).join(Shipment).filter(
                Shipment.user_id == user_id
            ).order_by(TrackingEvent.created_at.desc()).limit(limit).all()
            
            return [e.to_dict() for e in events]
        except Exception as e:
            logger.error(f"Error getting recent activity: {e}")
            return []