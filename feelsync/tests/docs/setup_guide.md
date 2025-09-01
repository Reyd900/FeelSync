# FeelSync Setup Guide

## Table of Contents
- [System Requirements](#system-requirements)
- [Development Environment Setup](#development-environment-setup)
- [Production Deployment](#production-deployment)
- [Docker Setup](#docker-setup)
- [Database Configuration](#database-configuration)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

## System Requirements

### Minimum Requirements
- **Python**: 3.8+
- **RAM**: 4GB
- **Storage**: 10GB free space
- **OS**: Windows 10, macOS 10.14+, or Linux (Ubuntu 18.04+)

### Recommended Requirements
- **Python**: 3.9+
- **RAM**: 8GB
- **Storage**: 20GB free space
- **Database**: PostgreSQL 12+ (production)

### Dependencies
- Node.js 16+ (for frontend build tools)
- Git
- PostgreSQL or SQLite
- Redis (optional, for caching)

## Development Environment Setup

### 1. Clone the Repository
```bash
git clone https://github.com/your-org/feelsync.git
cd feelsync
```

### 2. Create Virtual Environment
```bash
# Using venv (recommended)
python -m venv feelsync_env

# Activate environment
# On Windows:
feelsync_env\Scripts\activate
# On macOS/Linux:
source feelsync_env/bin/activate
```

### 3. Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Environment Configuration
Create a `.env` file in the project root:

```bash
# Copy example environment file
cp .env.example .env
```

Edit `.env` with your configuration:
```env
# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DEBUG=True

# Database Configuration
DATABASE_URL=sqlite:///feelsync_dev.db
# For PostgreSQL:
# DATABASE_URL=postgresql://username:password@localhost:5432/feelsync_dev

# Security
WTF_CSRF_ENABLED=False
SESSION_COOKIE_SECURE=False

# Email Configuration (optional for development)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Redis Configuration (optional)
REDIS_URL=redis://localhost:6379

# ML Model Configuration
MODEL_PATH=./models/trained_models
TRAINING_DATA_PATH=./data

# Game Configuration
MAX_GAMES_PER_DAY=10
MIN_AGE_REQUIREMENT=13
MAX_AGE_REQUIREMENT=25
```

### 5. Database Setup
```bash
# Initialize database
python scripts/setup_database.py

# Generate sample data (optional)
python scripts/generate_sample_data.py
```

### 6. Train Initial ML Models
```bash
# Train models with sample data
python scripts/train_models.py
```

### 7. Run the Application
```bash
# Start development server
python app.py
```

The application will be available at `http://localhost:5000`

## Production Deployment

### 1. Server Setup (Ubuntu 20.04 LTS)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3-pip python3-venv nginx postgresql postgresql-contrib redis-server

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash -
sudo apt install -y nodejs
```

### 2. Database Setup (PostgreSQL)

```bash
# Create database user
sudo -u postgres createuser --interactive feelsync

# Create database
sudo -u postgres createdb feelsync_prod

# Set password
sudo -u postgres psql
\password feelsync
\q
```

### 3. Application Setup

```bash
# Create application directory
sudo mkdir -p /opt/feelsync
sudo chown $USER:$USER /opt/feelsync

# Clone and setup application
cd /opt/feelsync
git clone https://github.com/your-org/feelsync.git .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Production environment file
cp .env.example .env.production
```

Edit `.env.production`:
```env
FLASK_ENV=production
SECRET_KEY=generate-secure-random-key
DEBUG=False

DATABASE_URL=postgresql://feelsync:password@localhost:5432/feelsync_prod

WTF_CSRF_ENABLED=True
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True

# Add other production configurations...
```

### 4. Initialize Production Database

```bash
source venv/bin/activate
export FLASK_ENV=production
python scripts/setup_database.py
python scripts/train_models.py
```

### 5. Setup Gunicorn

Create `/etc/systemd/system/feelsync.service`:
```ini
[Unit]
Description=FeelSync Web Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/feelsync
Environment="PATH=/opt/feelsync/venv/bin"
EnvironmentFile=/opt/feelsync/.env.production
ExecStart=/opt/feelsync/venv/bin/gunicorn --workers 3 --bind unix:feelsync.sock -m 007 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Start and enable service
sudo systemctl start feelsync
sudo systemctl enable feelsync
sudo systemctl status feelsync
```

### 6. Configure Nginx

Create `/etc/nginx/sites-available/feelsync`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        include proxy_params;
        proxy_pass http://unix:/opt/feelsync/feelsync.sock;
    }

    location /static {
        alias /opt/feelsync/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/feelsync /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

### 7. SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## Docker Setup

### 1. Using Docker Compose (Recommended)

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=development
      - DATABASE_URL=postgresql://feelsync:password@db:5432/feelsync
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - ./:/app
      - ./uploads:/app/uploads

  db:
    image: postgres:13
    environment:
      - POSTGRES_USER=feelsync
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=feelsync
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./static:/var/www/static
    depends_on:
      - web

volumes:
  postgres_data:
```

Create `Dockerfile`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories
RUN mkdir -p uploads logs models/trained_models

# Set environment variables
ENV FLASK_APP=app.py
ENV PYTHONPATH=/app

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/ || exit 1

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "3", "app:app"]
```

### 2. Build and Run

```bash
# Build and start services
docker-compose up --build

# Run database migrations
docker-compose exec web python scripts/setup_database.py

# Generate sample data
docker-compose exec web python scripts/generate_sample_data.py
```

## Database Configuration

### SQLite (Development)
```python
# config.py
SQLALCHEMY_DATABASE_URI = 'sqlite:///feelsync.db'
```

### PostgreSQL (Production)
```python
# config.py
SQLALCHEMY_DATABASE_URI = 'postgresql://username:password@localhost:5432/feelsync'
```

### Database Migrations

```bash
# Create migration
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Or using custom script
python scripts/setup_database.py
```

### Database Backup

```bash
# PostgreSQL backup
pg_dump feelsync_prod > feelsync_backup.sql

# Restore
psql feelsync_prod < feelsync_backup.sql

# SQLite backup
cp feelsync.db feelsync_backup.db
```

## Testing

### 1. Setup Test Environment

```bash
# Install test dependencies (included in requirements.txt)
pip install pytest pytest-flask pytest-cov

# Create test database
export FLASK_ENV=testing
python scripts/setup_database.py
```

### 2. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest -v
```

### 3. Test Configuration

Create `pytest.ini`:
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --strict-markers --disable-warnings
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    unit: marks tests as unit tests
```

## Monitoring and Logging

### 1. Application Logs

```bash
# View logs
tail -f logs/feelsync.log

# Rotate logs
sudo logrotate /etc/logrotate.d/feelsync
```

### 2. System Monitoring

```bash
# Install monitoring tools
sudo apt install htop iotop nethogs

# Monitor application
sudo systemctl status feelsync
journalctl -u feelsync -f
```

### 3. Database Monitoring

```bash
# PostgreSQL stats
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"

# Database size
sudo -u postgres psql -c "SELECT pg_size_pretty(pg_database_size('feelsync_prod'));"
```

## Performance Optimization

### 1. Database Optimization

```sql
-- Add indexes for common queries
CREATE INDEX idx_game_sessions_user_started ON game_sessions(user_id, started_at);
CREATE INDEX idx_behavior_data_session_timestamp ON behavior_data(session_id, timestamp);
CREATE INDEX idx_analysis_reports_user_generated ON analysis_reports(user_id, generated_at);
```

### 2. Redis Caching

```python
# config.py
CACHE_TYPE = "redis"
CACHE_REDIS_URL = "redis://localhost:6379/0"
CACHE_DEFAULT_TIMEOUT = 300
```

### 3. Static File Serving

```nginx
# nginx.conf
location /static {
    alias /opt/feelsync/static;
    expires 1y;
    add_header Cache-Control "public, immutable";
    gzip on;
    gzip_types text/css application/javascript image/svg+xml;
}
```

## Security Configuration

### 1. Environment Variables

```env
# Generate secure keys
SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex())')
DATABASE_PASSWORD=$(openssl rand -base64 32)
```

### 2. Firewall Setup

```bash
# Configure UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

### 3. SSL/TLS Configuration

```nginx
# Strong SSL configuration
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384;
ssl_prefer_server_ciphers off;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
```

## Backup and Recovery

### 1. Database Backup Script

Create `scripts/backup_database.sh`:
```bash
#!/bin/bash
BACKUP_DIR="/opt/backups/feelsync"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/feelsync_backup_$DATE.sql"

mkdir -p $BACKUP_DIR
pg_dump feelsync_prod > $BACKUP_FILE
gzip $BACKUP_FILE

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
```

### 2. Automated Backups

```bash
# Add to crontab
crontab -e
# Add: 0 2 * * * /opt/feelsync/scripts/backup_database.sh
```

### 3. Application Data Backup

```bash
# Backup uploaded files and models
tar -czf feelsync_data_backup.tar.gz uploads/ models/trained_models/ logs/
```

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   ```bash
   # Check PostgreSQL status
   sudo systemctl status postgresql
   
   # Check connection
   psql -U feelsync -d feelsync_prod -h localhost
   ```

2. **Permission Errors**
   ```bash
   # Fix file permissions
   sudo chown -R www-data:www-data /opt/feelsync
   sudo chmod -R 755 /opt/feelsync
   ```

3. **Memory Issues**
   ```bash
   # Check memory usage
   free -h
   
   # Restart services
   sudo systemctl restart feelsync
   ```

4. **SSL Certificate Issues**
   ```bash
   # Check certificate status
   sudo certbot certificates
   
   # Renew certificate
   sudo certbot renew --dry-run
   ```

### Log Analysis

```bash
# Application errors
grep -i error logs/feelsync.log

# Database errors
sudo tail -f /var/log/postgresql/postgresql-13-main.log

# Nginx errors
sudo tail -f /var/log/nginx/error.log
```

### Health Checks

```bash
# Application health
curl http://localhost:5000/health

# Database health
python -c "from app import db; print(db.engine.execute('SELECT 1').scalar())"

# Redis health
redis-cli ping
```

## Support and Resources

- **Documentation**: https://docs.feelsync.com
- **Issues**: https://github.com/your-org/feelsync/issues
- **Discord**: https://discord.gg/feelsync
- **Email**: support@feelsync.com

## Next Steps

After successful setup:

1. **Configure monitoring and alerting**
2. **Set up automated backups**
3. **Configure CI/CD pipeline**
4. **Review security settings**
5. **Load test the application**
6. **Train production ML models with real data**
