# ⚡ Quick Start Guide

## 1️⃣ Setup (2 minutes)

```bash
# Make setup script executable
chmod +x setup.sh

# Run setup
./setup.sh

# Activate virtual environment
source venv/bin/activate
```

## 2️⃣ Configure Kedro Path

Edit `.env` and update:

```bash
KEDRO_PROJECT_PATH=/path/to/your/kedro/project
```

Or edit `app/tasks.py` line 40:

```python
KEDRO_PROJECT_PATH = '/path/to/your/kedro/project'
```

## 3️⃣ Start Services

### Terminal 1: Redis

```bash
redis-server
```

### Terminal 2: Celery Worker

```bash
source venv/bin/activate
celery -A worker worker --loglevel=info
```

### Terminal 3: FastAPI

```bash
source venv/bin/activate
python main.py
```

## 4️⃣ Test API

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Submit job
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "pipeline_name": "data_loading",
    "parameters": {}
  }'

# Check job status (replace with actual job ID)
curl http://localhost:8000/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000
```

## 📊 Expected Output

### Celery Terminal (should show):

```
Task app.tasks.execute_pipeline[...] received
📤 Calling external Kedro project at: /path/to/kedro
📋 Running command: kedro run --pipeline data_loading
✅ Pipeline executed successfully
```

### FastAPI Terminal (should show):

```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     🚀 Job submission started
INFO:     ✅ Job created: 550e8400-...
INFO:     📤 Sending task to Celery...
```

## ✅ Success Indicators

- ✅ Redis responds to `redis-cli ping`
- ✅ Celery shows "celery@<hostname> ready"
- ✅ FastAPI shows "Uvicorn running"
- ✅ HTTP POST returns 202 status code
- ✅ Job status changes from "pending" to "completed"

## 🐛 Troubleshooting

**Q: Connection refused to Redis?**
```bash
# Start Redis in another terminal
redis-server
```

**Q: ModuleNotFoundError?**
```bash
pip install -r requirements.txt
```

**Q: Kedro project not found?**
- Check KEDRO_PROJECT_PATH in .env
- Verify path exists: `ls /path/to/kedro/kedro.yml`

**Q: Jobs stuck on "pending"?**
- Check Celery worker is running
- Check Redis has messages: `redis-cli LLEN celery`

---

**Need help?** See `README.md` or `IMPLEMENTATION_SUMMARY.md`
