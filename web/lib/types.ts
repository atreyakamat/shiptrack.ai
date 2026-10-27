export type Status =
  | "BOOKED" | "IN_TRANSIT" | "OUT_FOR_DELIVERY" | "DELIVERED" | "EXCEPTION" | "UNKNOWN";

export interface Shipment {
  id: number;
  tracking_number: string;
  carrier: string;
  description: string | null;
  category: string;
  status: Status;
  current_location: string | null;
  origin: string | null;
  destination: string | null;
  last_updated: string | null;
  expected_delivery: string | null;
  priority: string;
  notes: string | null;
  is_archived: boolean;
  article_type: string | null;
  last_successful_sync: string | null;
  last_error: string | null;
  created_at: string;
  events?: TrackingEvent[];
}

export interface TrackingEvent {
  id: number;
  status: string;
  location: string | null;
  description: string | null;
  event_timestamp: string | null;
  created_at: string;
}

export interface AiSummary {
  summary: string;
  health_status: string;
  delay_analysis: string;
  prediction: string;
  model: string;
}

export interface Insights {
  summary: string;
  total_count: number;
  delivered_count: number;
  delayed_count: number;
  watch_count: number;
  normal_count: number;
  recommendations: string[];
  delayed_shipments: { id: number; tracking_number: string; status: string; current_location: string | null }[];
}

export interface Analytics {
  overview: { total: number; delivered: number; in_transit: number; delayed: number; delivery_rate: number; avg_time: number };
  by_status: { status: string; count: number }[];
  shipments_over_time: { period: string; count: number }[];
  avg_delivery_by_carrier: { carrier: string; avg_days: number; count: number }[];
  common_locations: { location: string; count: number }[];
  stale_shipments: { id: number; tracking_number: string; status: string }[];
}

export interface AppNotification {
  id: number;
  shipment_id: number | null;
  channel: string;
  notification_type: string;
  message: string;
  status: string;
  created_at: string | null;
}

export interface User { id: number; email: string }
