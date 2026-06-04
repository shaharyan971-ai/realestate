# 🚀 Deployment Guide for Real Estate Marketplace

## 1. Environment Variables (.env)
Copy `.env.example` to `.env` and fill in all secrets:
- MongoDB Atlas connection
- Stripe & Razorpay keys
- SendGrid/SMTP credentials
- Cloudinary keys
- CORS origins (frontend/backend URLs)
- Feature flags (enable/disable services)

## 2. Backend Deployment (Render or Docker)
### Render
- Connect your GitHub repo to Render.com
- Add all `.env` variables in Render dashboard
- Set Python version: 3.10+
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- Set up auto-deploy on push to main branch

### Docker (Manual)
- Build: `docker build -t realestate-api .`
- Run: `docker run -p 8000:8000 --env-file .env realestate-api`

## 3. Frontend Deployment (Vercel)
- Connect frontend directory to Vercel
- Set environment variables for API URLs
- Deploy (auto or manual)

## 4. MongoDB Atlas
- Create cluster, user, and whitelist IPs
- Use connection string in `.env`

## 5. Webhooks
- Stripe: Add endpoint `/api/payments/webhook/stripe` in Stripe dashboard
- Razorpay: Add endpoint `/api/payments/webhook/razorpay` in Razorpay dashboard
- Copy signing secrets to `.env`

## 6. CORS Setup
- Set `ALLOWED_ORIGINS` in `.env` to your frontend and backend URLs
- Ensure CORS is enabled in FastAPI config

## 7. Production Build Steps
- Set `ENV=production` in `.env`
- Use HTTPS (enforce in production)
- Monitor logs and errors (Sentry, Datadog, etc.)
- Run all tests before go-live

## 8. Post-Deployment
- Test all payment flows and webhooks
- Test subscription, booking, agent, and admin features
- Monitor performance and error logs
- Update documentation as needed

---

**Reference:**
- See `.env.example` for all required variables
- See TESTING_CHECKLIST.md for go-live validation
- See SCALABILITY_NOTES.md for scaling tips
