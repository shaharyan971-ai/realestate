# 🧪 Production Testing Checklist for Real Estate Marketplace

## 1. Payment System
- [ ] Stripe checkout: success, cancel, webhook
- [ ] Razorpay checkout: UPI, card, netbanking, webhook
- [ ] Booking fee, premium listing, featured upgrade, agent subscription
- [ ] Payment status updates in MongoDB
- [ ] Webhook signature verification (Stripe/Razorpay)
- [ ] Transaction logs and error handling

## 2. Subscription System
- [ ] Plan purchase (Basic, Pro, Enterprise)
- [ ] Plan feature limits enforced (listings, visibility)
- [ ] Subscription expiry/renewal logic
- [ ] Auto-disable features on expiry
- [ ] Payment status and plan activation

## 3. Booking System
- [ ] Book property flow (user → pay → booking stored)
- [ ] Agent notification on booking
- [ ] Booking status and payment status updates
- [ ] Booking dashboard metrics

## 4. Agent System
- [ ] Agent registration and KYC
- [ ] Agent profile page (public)
- [ ] Commission tracking and earnings dashboard
- [ ] Agent rating and reviews

## 5. Admin Dashboard
- [ ] Revenue and analytics metrics
- [ ] Monthly revenue chart
- [ ] Active subscriptions, bookings count
- [ ] Top agents and commission analytics

## 6. Advanced Features
- [ ] Property filtering, price slider, bedrooms/bathrooms
- [ ] Google Maps, amenities, mortgage calculator
- [ ] Floor plan upload (PDF), virtual tour, multi-image upload

## 7. Security
- [ ] JWT authentication (all roles)
- [ ] Role-based access (admin/agent/user)
- [ ] Protected routes (backend + frontend)
- [ ] Input validation (Pydantic)
- [ ] Rate limiting
- [ ] Secure .env and HTTPS config

## 8. Email & Notifications
- [ ] Booking confirmation, payment success, expiry reminders
- [ ] Property approval, admin alerts
- [ ] Email delivery (SendGrid/SMTP)

## 9. UI/UX
- [ ] Payment success animation, toast notifications
- [ ] Loading skeletons, smooth transitions
- [ ] Status badges, premium highlight, animated upgrade

## 10. Database
- [ ] Indexes on all major collections
- [ ] Data integrity for users, agents, properties, bookings, payments, subscriptions, transactions, notifications

## 11. Deployment
- [ ] .env structure and secrets
- [ ] Webhook endpoints live and secure
- [ ] CORS setup for frontend/backend
- [ ] Production build (Vercel/Render/MongoDB Atlas)

## 12. General
- [ ] All API endpoints tested (manual + automated)
- [ ] Error handling and logging
- [ ] Scalability and load testing
- [ ] Documentation up to date
