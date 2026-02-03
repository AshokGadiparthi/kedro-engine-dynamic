# ✅ COMPLETE INSTALLATION GUIDE

## Quick Start (5 Minutes)

```bash
# 1. Extract project
unzip ml-platform-complete.zip
cd ml-platform-complete

# 2. Create environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install --upgrade pip setuptools
pip install -r requirements.txt

# 4. Initialize database
python -c "from app.core.database import Base, engine; Base.metadata.create_all(bind=engine)"

# 5. Run application
python main.py

# 6. Visit API
# Open: http://localhost:8000/docs
```

## Detailed Setup

### 1. System Requirements
- Python 3.8+
- pip 23.0+
- 2GB RAM minimum
- 2GB disk space

### 2. Create Virtual Environment

```bash
python -m venv venv

# Activate:
# Linux/Mac: source venv/bin/activate
# Windows: venv\Scripts\activate
```

### 3. Install All Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Initialize Database

```bash
# Run initialization
python << 'EOF'
from app.core.database import Base, engine
Base.metadata.create_all(bind=engine)
print("✅ Database initialized!")
