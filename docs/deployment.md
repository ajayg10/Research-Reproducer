# Deployment Guide

## Prerequisites

- Google Cloud Platform account
- gcloud CLI installed and configured
- Docker installed locally
- Python 3.11+
- Node.js 18+

## Local Development Setup

### 1. Clone Repository
```bash
git clone <repository-url>
cd Researchreproducability
```

### 2. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp ../.env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 3. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Create .env file if needed
echo "VITE_API_URL=http://localhost:8000/api" > .env
```

### 4. Docker Setup

Pull the Python base image for sandbox:
```bash
docker pull python:3.11-slim
```

### 5. Start Services

**Option A: Run separately**
```bash
# Terminal 1 - Backend
cd backend
python main.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

**Option B: Docker Compose**
```bash
docker-compose -f docker/docker-compose.yml up --build
```

### 6. Access Application
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Google Cloud Deployment

### 1. Project Setup

```bash
# Set project ID
export PROJECT_ID="your-gcp-project-id"
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable \
  run.googleapis.com \
  containerregistry.googleapis.com \
  cloudbuild.googleapis.com \
  aiplatform.googleapis.com \
  firestore.googleapis.com \
  storage.googleapis.com
```

### 2. Create Resources

```bash
# Create Firestore database
gcloud firestore databases create --location=us-central1

# Create Cloud Storage bucket
gsutil mb -l us-central1 gs://${PROJECT_ID}-reproducibility

# Create service account for Cloud Run
gcloud iam service-accounts create reproducibility-engine \
  --display-name="Reproducibility Engine Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:reproducibility-engine@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:reproducibility-engine@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/datastore.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:reproducibility-engine@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/storage.admin"
```

### 3. Setup Secrets

```bash
# Store Gemini API key in Secret Manager
gcloud secrets create gemini-api-key --replication-policy="automatic"
echo -n "your-gemini-api-key" | gcloud secrets versions add gemini-api-key --data-file=-

# Grant service account access to secret
gcloud secrets add-iam-policy-binding gemini-api-key \
  --member="serviceAccount:reproducibility-engine@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### 4. Build and Deploy Backend

```bash
# Build container
gcloud builds submit --tag gcr.io/$PROJECT_ID/reproducibility-backend \
  --dockerfile=docker/Dockerfile.backend .

# Deploy to Cloud Run
gcloud run deploy reproducibility-backend \
  --image gcr.io/$PROJECT_ID/reproducibility-backend \
  --platform managed \
  --region us-central1 \
  --service-account reproducibility-engine@${PROJECT_ID}.iam.gserviceaccount.com \
  --set-env-vars ENVIRONMENT=production,STORAGE_TYPE=gcs,GCS_BUCKET=${PROJECT_ID}-reproducibility \
  --set-secrets GEMINI_API_KEY=gemini-api-key:latest \
  --memory 2Gi \
  --cpu 2 \
  --timeout 900 \
  --max-instances 10 \
  --allow-unauthenticated
```

### 5. Get Backend URL

```bash
export BACKEND_URL=$(gcloud run services describe reproducibility-backend \
  --region us-central1 \
  --format 'value(status.url)')

echo "Backend URL: $BACKEND_URL"
```

### 6. Deploy Frontend

```bash
# Build frontend with production API URL
cd frontend
VITE_API_URL=${BACKEND_URL}/api npm run build

# Deploy to Cloud Storage as static site
gsutil -m cp -r dist/* gs://${PROJECT_ID}-reproducibility-frontend/

# Make bucket public
gsutil iam ch allUsers:objectViewer gs://${PROJECT_ID}-reproducibility-frontend

# Enable website configuration
gsutil web set -m index.html -e index.html gs://${PROJECT_ID}-reproducibility-frontend

echo "Frontend URL: https://storage.googleapis.com/${PROJECT_ID}-reproducibility-frontend/index.html"
```

### 7. (Optional) Setup Custom Domain

```bash
# Setup Load Balancer and SSL certificate
# Follow: https://cloud.google.com/storage/docs/hosting-static-website
```

## Environment Variables

### Backend (.env)
```bash
# Required
GEMINI_API_KEY=your_key_here

# Optional (has defaults)
GEMINI_MODEL=gemini-2.0-flash-exp
GOOGLE_CLOUD_PROJECT=your-project-id
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
ENVIRONMENT=local
STORAGE_TYPE=local
STORAGE_PATH=./storage
SANDBOX_TIMEOUT=600
MAX_RETRIES=3
LOG_LEVEL=INFO
```

### Frontend (.env)
```bash
VITE_API_URL=http://localhost:8000/api  # Local
# or
VITE_API_URL=https://your-backend-url.run.app/api  # Production
```

## Monitoring and Logging

### View Logs
```bash
# Cloud Run logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=reproducibility-backend" \
  --limit 50 \
  --format json

# Stream logs
gcloud alpha run services logs tail reproducibility-backend --region us-central1
```

### Monitoring Dashboard
- Navigate to Cloud Console → Cloud Run → reproducibility-backend
- View metrics: request count, latency, errors, memory usage

## Scaling Configuration

### Cloud Run Auto-Scaling
```bash
# Update scaling settings
gcloud run services update reproducibility-backend \
  --region us-central1 \
  --min-instances 1 \
  --max-instances 10 \
  --concurrency 10
```

### For Heavy Workloads: GKE Jobs

For papers requiring GPU or longer execution:

```bash
# Create GKE cluster
gcloud container clusters create reproducibility-cluster \
  --region us-central1 \
  --machine-type n1-standard-4 \
  --num-nodes 1 \
  --enable-autoscaling \
  --min-nodes 1 \
  --max-nodes 5

# Update executor agent to use GKE Jobs instead of local Docker
# (Implementation TBD)
```

## Troubleshooting

### Backend won't start
```bash
# Check logs
docker logs <container-id>

# Verify Gemini API key
python -c "import google.generativeai as genai; genai.configure(api_key='YOUR_KEY'); print('OK')"
```

### Sandbox execution fails
```bash
# Check Docker is running
docker ps

# Verify python:3.11-slim image
docker pull python:3.11-slim

# Check Docker permissions (Linux)
sudo usermod -aG docker $USER
```

### Frontend can't connect to backend
- Check CORS settings in backend/main.py
- Verify VITE_API_URL in frontend .env
- Check network/firewall settings

## Cost Optimization

### Estimated Costs (MVP)
- Cloud Run: ~$10-20/month (with low traffic)
- Firestore: ~$1-5/month
- Cloud Storage: ~$1/month
- Gemini API: ~$5-50/month (depending on usage)
- **Total: ~$20-80/month**

### Cost Reduction Tips
1. Use Cloud Run min-instances=0 for dev
2. Enable request-response caching
3. Optimize Gemini token usage
4. Use Cloud Storage lifecycle policies
5. Set spending alerts

## Security Checklist

- [ ] Gemini API key stored in Secret Manager
- [ ] Service account follows least-privilege
- [ ] Cloud Run requires authentication (or carefully allow public)
- [ ] CORS configured correctly
- [ ] Sandbox isolation verified
- [ ] No secrets in code or logs
- [ ] Environment variables not exposed
- [ ] Regular security updates

## Backup and Recovery

### Backup Firestore
```bash
gcloud firestore export gs://${PROJECT_ID}-reproducibility/backups/$(date +%Y%m%d)
```

### Backup Cloud Storage
```bash
gsutil -m rsync -r gs://${PROJECT_ID}-reproducibility gs://${PROJECT_ID}-reproducibility-backup
```

## Updating Deployment

```bash
# Rebuild and redeploy backend
gcloud builds submit --tag gcr.io/$PROJECT_ID/reproducibility-backend \
  --dockerfile=docker/Dockerfile.backend .

gcloud run deploy reproducibility-backend \
  --image gcr.io/$PROJECT_ID/reproducibility-backend \
  --region us-central1

# Rebuild and redeploy frontend
cd frontend
npm run build
gsutil -m rsync -r dist/ gs://${PROJECT_ID}-reproducibility-frontend/
```

## Support

For issues or questions:
- Check logs: backend and Docker
- Review API documentation: http://localhost:8000/docs
- Verify environment variables
- Check Docker/network connectivity
