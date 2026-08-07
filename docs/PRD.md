# Product Requirements Document (PRD)

## ShipTrack AI – Intelligent Shipment Management & Tracking Platform

**Version:** 1.0  
**Status:** Product Definition  
**Author:** Atreya Kamat  
**Target Users:** Individuals, Small Businesses, E-commerce Sellers, Document Couriers, Logistics Managers

---

## 1. Executive Summary

ShipTrack AI is an intelligent shipment management platform designed to centralize parcel tracking across India Post (initially) while providing analytics, OCR-powered receipt ingestion, AI-generated shipment summaries, and future multi-carrier support.

Unlike traditional tracking websites that only display a shipment's current status, ShipTrack AI creates a historical database of all shipments, visualizes delivery performance, generates actionable insights, and automates shipment monitoring.

The long-term vision is to become a unified logistics intelligence platform supporting multiple courier providers with AI-powered delivery analytics and automation.

---

## 2. Problem Statement

Current shipment tracking suffers from several limitations:

- Users must manually enter tracking IDs every time.
- Historical tracking information is not retained.
- No centralized dashboard for multiple shipments.
- No delivery analytics or performance metrics.
- Tracking receipts are difficult to organize.
- No intelligent summaries or proactive notifications.
- No OCR-based automation from shipment receipts.
- No easy integration with messaging platforms.

ShipTrack AI addresses these limitations by creating a persistent shipment management system rather than a one-time tracking tool.

---

## 3. Product Vision

> "Build the personal logistics dashboard that every frequent shipper wishes India Post already provided."

The platform should allow users to:

- Store unlimited tracking IDs
- Automatically fetch shipment updates
- View complete shipment history
- Analyze delivery performance
- Receive intelligent notifications
- Upload postal receipts instead of manually typing tracking IDs
- Understand shipment progress through AI-generated summaries

---

## 4. Objectives

### Primary Goals

- Simplify shipment tracking
- Eliminate repetitive manual lookups
- Build historical shipment records
- Provide delivery analytics
- Reduce manual data entry using OCR
- Improve shipment visibility through AI

### Secondary Goals

- Multi-courier support
- WhatsApp notifications
- Smart delivery predictions
- Business shipment management
- Mobile responsiveness

---

## 5. Target Users

### Individual Users

- Passport tracking
- Government document tracking
- Online shopping
- Personal parcels

### Small Businesses

- Sticker businesses
- Handmade sellers
- Etsy sellers
- Instagram businesses

### E-commerce Sellers

- Track customer shipments
- Monitor delivery success
- Average delivery time
- Delivery analytics

### Courier-heavy Users

- Lawyers
- CA firms
- Government offices
- Educational institutions

---

## 6. Product Scope

### In Scope

- India Post Tracking
- Shipment Dashboard
- Tracking History
- OCR Receipt Scanner
- AI Summaries
- Analytics
- Notifications
- Export

### Out of Scope (Version 1)

- Payment integrations
- Courier booking
- Route optimization
- Live GPS tracking
- Delivery personnel tracking

---

## 7. User Stories

### Add Shipment

As a user, I want to enter a tracking ID so that I can monitor the shipment.

### OCR Upload

As a user, I want to upload my postal receipt so that the tracking number is detected automatically.

### AI Summary

As a user, I want AI to summarize shipment progress so that I don't have to interpret every tracking event.

### Analytics

As a business owner, I want delivery performance reports so I can understand courier efficiency.

### Notifications

As a user, I want WhatsApp updates so I know immediately when shipment status changes.

---

## 8. Functional Requirements

### Module 1 — Authentication

Features:

- Register
- Login
- Forgot Password
- JWT Authentication
- Session Management

### Module 2 — Dashboard

Display:

- Total Shipments
- Active Shipments
- Delivered
- Delayed
- Average Delivery Time
- Last Refresh Time

Widgets:

- Shipment Status Pie Chart
- Monthly Deliveries
- Delivery Timeline
- Recent Shipments

### Module 3 — Shipment Management

Add Shipment fields:

- Tracking Number
- Description
- Category
- Carrier
- Notes
- Priority
- Expected Delivery

Edit Shipment supports:

- Description
- Category
- Priority
- Notes

Archive Shipment:

- Soft delete

Delete Shipment:

- Permanent removal

### Module 4 — Tracking Engine

Workflow:

```text
Tracking ID
↓
India Post Website
↓
Submit Tracking
↓
Retrieve Data
↓
Parse
↓
Normalize
↓
Store Database
```

Supported data:

- Current Status
- Current Location
- Last Updated
- Booking Date
- Destination
- Tracking History

Refresh options:

- Manual Refresh
- Refresh All
- Scheduled Refresh

### Module 5 — Tracking History

Store every event:

```text
Booked
↓
Dispatched
↓
Bag Received
↓
Transit
↓
Out for Delivery
↓
Delivered
```

Each event contains:

- Timestamp
- Location
- Status
- Description

### Module 6 — OCR Engine

Supported inputs:

- Image
- PDF
- Scanned Receipt

Workflow:

```text
Upload
↓
Image Processing
↓
OCR
↓
Regex
↓
Tracking Number
↓
Validation
↓
Shipment Created
```

Extract:

- Tracking Number
- Booking Date
- Post Office
- Destination
- Article Type

### Module 7 — AI Insights

Generate:

- Shipment Summary
- Delay Explanation
- Delivery Prediction
- Monthly Report
- Shipment Health Score

Examples:

> Shipment has reached the destination sorting office.  
> Delivery is expected within one business day.  
> Shipment has remained at Panaji NSH longer than average.

### Module 8 — Analytics

Charts:

- Delivery Status
- Monthly Shipments
- Transit Duration
- Delivery Heatmap
- Most Frequent Locations
- Delivery Trend
- Average Stops
- Courier Performance

KPIs:

- Average Delivery Time
- Average Transit Time
- Delayed Shipments
- Fastest Delivery
- Slowest Delivery
- Total Tracking Events

### Module 9 — Notifications

Channels:

- Email
- WhatsApp
- Push Notification (Future)

Events:

- Shipment Added
- Status Changed
- Delivered
- Delayed
- Refresh Completed
- OCR Completed

### Module 10 — Search

Search by:

- Tracking Number
- Description
- Location
- Category
- Status
- Date
- Carrier

Filters:

- Delivered
- Transit
- Today
- Last Week
- Government
- Archived

### Module 11 — Export

Export:

- CSV
- Excel
- PDF
- JSON

### Module 12 — Admin

- System Health
- Refresh Logs
- OCR Logs
- User Management
- API Usage
- Notification Logs

---

## 9. AI Features

### Shipment Summary

Input: Tracking Events  
Output: Natural language summary

### Delivery Prediction

Predict:

- Expected delivery date
- Confidence score

### Delay Detection

AI flags:

- Long idle periods
- Repeated scans
- Routing anomalies

### Conversational Search

Examples:

- "Show delayed shipments"
- "Show passport parcels"
- "Which parcel will arrive first?"

---

## 10. OCR Features

Supported formats:

- JPG
- PNG
- PDF

Detection:

- Tracking Number
- Destination
- Booking Date
- Office Name
- Article Type

Validation regex:

```regex
[A-Z]{2}[0-9]{9}IN
```

---

## 11. Notification Examples

WhatsApp:

```text
📦 Shipment Update

Tracking:
EM740043207IN

Status:
Out for Delivery

Location:
Bambavada SO

Time:
09:07 AM
```

Daily Summary:

```text
Today's Shipments

2 Delivered

1 Transit

1 Delayed
```

---

## 12. Database Schema

Entities:

- Users
- Shipments
- TrackingEvents
- OCRDocuments
- Notifications
- RefreshLogs
- AISummaries
- Settings

Relationship:

```text
User
│
├── Shipments
│      │
│      ├── Tracking Events
│      ├── OCR
│      ├── AI Summary
│      └── Notifications
```

---

## 13. Technology Stack

### Backend

- Python
- Flask
- SQLAlchemy
- Celery / APScheduler
- Playwright

### Frontend

- Streamlit
- Bootstrap
- Plotly

### OCR

- EasyOCR
- OpenCV
- Regex

### Database

Development:

- SQLite

Production:

- PostgreSQL

### AI

- OpenRouter (Cloud) or Ollama (Local)
- Models: Llama, Qwen, Mistral

### Notifications

- WhatsApp Business Cloud API
- SMTP

### Deployment

- Docker
- Nginx
- Gunicorn
- Linux VPS

---

## 14. Security

- JWT Authentication
- Password Hashing
- Rate Limiting
- Encrypted Secrets
- Input Validation
- Secure File Upload
- SQL Injection Protection
- CSRF Protection

---

## 15. Future Roadmap

### Phase 1

- Manual Tracking
- Dashboard
- History
- Refresh

### Phase 2

- OCR
- AI Summary
- Analytics
- Export

### Phase 3

- WhatsApp
- Email
- Auto Refresh
- Delay Alerts

### Phase 4

- Multi-carrier Support
- Mobile App
- API
- Teams
- Shared Workspaces

### Phase 5

- Smart Predictions
- Delivery Scoring
- ML Delay Prediction
- Shipment Recommendations
- Business Analytics

---

## 16. Success Metrics

User metrics:

- Average tracking lookup time < 3 seconds (excluding source site latency)
- OCR accuracy > 95% for clear India Post receipts
- AI summary generation < 2 seconds (cached/local) or acceptable API latency
- Dashboard load time < 2 seconds
- User retention for saved shipments

Product metrics:

- 100% historical tracking retention
- Zero duplicate tracking events after refresh
- Successful tracking refresh rate > 98%
- Notification delivery success > 99%

---

## 17. Long-Term Vision

ShipTrack AI evolves from an India Post tracking assistant into a **unified Shipment Intelligence Platform**. By introducing a pluggable carrier architecture (e.g., India Post, Blue Dart, DTDC, Delhivery, India Post EMS), OCR-powered receipt ingestion, AI-driven analytics, and omnichannel notifications, it becomes a comprehensive logistics companion for individuals and businesses. The core differentiator is not simply tracking parcels—it is building a persistent, searchable, and intelligent knowledge base of shipment history that provides insights, automation, and operational value over time.
