
# 🚀 Deployment Instructions

## Render.com Deployment

### Prerequisites
1. **Neon Database** - PostgreSQL database URL
2. **Environment Variables** - All API keys and secrets

### Setup Steps

1. **Connect GitHub Repository**
   - Push your code to GitHub
   - Connect Render to your GitHub repository

2. **Configure Environment Variables in Render Dashboard:**
   ```
   FLASK_ENV=production
   DEBUG=false
   SECRET_KEY=your-secret-key-here
   SESSION_SECRET=your-session-secret-here
   DATABASE_URL=your-neon-database-url
   OPENROUTER_API_KEY=your-openrouter-key
   STRIPE_SECRET_KEY=your-stripe-secret-key
   VITE_STRIPE_PUBLIC_KEY=your-stripe-public-key
   ENCRYPTION_KEY=your-encryption-key
   ```

3. **Deployment Configuration**
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
   - **Auto-deploy:** Enable for main branch

### Neon Database Connection

1. **Get Database URL from Neon:**
   - Go to your Neon dashboard
   - Copy the connection string
   - Format: `postgresql://username:password@hostname/database`

2. **Set DATABASE_URL in Render:**
   - Add the full Neon connection string as `DATABASE_URL`

### Health Check
- Health check endpoint: `/`
- The app will automatically create database tables on first run

### Troubleshooting
- Check logs in Render dashboard
- Verify all environment variables are set
- Ensure Neon database is accessible

## Alternative: Replit Deployments (Recommended)

For easier deployment, consider using **Replit Deployments**:
1. Click "Deploy" button in Replit
2. Choose "Autoscale" deployment
3. Configure with existing environment variables
4. Deploy directly from Replit
