# Taskflow Manager

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![Docker](https://img.shields.io/badge/Docker-Supported-blue.svg)](https://www.docker.com/)

A comprehensive, cloud-ready Task Management System built with Flask, featuring enterprise-grade security, performance optimization, and collaboration tool integrations. This system provides a scalable solution for managing tasks, users, and team collaboration with modern authentication, caching, and notification capabilities.

## 🌟 Features

### Core Task Management
- **Complete CRUD Operations**: Create, read, update, and delete tasks with ease
- **Task Organization**: Categorize tasks by work, personal, or custom categories
- **Priority Management**: Set and manage task priorities (Low, Medium, High, Critical)
- **Due Date Tracking**: Assign and track task deadlines
- **Status Management**: Track task progress (Pending, In Progress, Completed, Archived)
- **Task Assignment**: Assign tasks to team members and track ownership

### User Management & Security
- **JWT-based Authentication**: Secure token-based authentication system
- **OAuth2 Integration**: Support for Google and other OAuth providers
- **Role-based Access Control**: Admin, Team Leader, and Regular User roles
- **Password Security**: Bcrypt hashing with salt for password security
- **Session Management**: Secure session handling with configurable expiry
- **Rate Limiting**: API endpoint protection against abuse

### Performance & Scalability
- **Redis Caching**: High-performance caching for frequently accessed data
- **Database Indexing**: Optimized database queries with strategic indexing
- **Load Balancer Ready**: Architecture designed for horizontal scaling
- **Connection Pooling**: Efficient database connection management
- **Async Processing**: Background task processing capabilities

### Collaboration & Integration
- **Slack Integration**: Real-time notifications and task management from Slack
- **Email Notifications**: Automated email alerts for task updates
- **Dashboard Analytics**: Team productivity metrics and insights
- **API Documentation**: Complete Swagger/OpenAPI documentation

### Cloud Deployment
- **Multi-environment Support**: Development, staging, and production configurations
- **Docker Containerization**: Complete Docker and docker-compose setup
- **AWS Integration**: Ready for deployment on AWS (EC2, RDS, ElastiCache)
- **Environment Management**: Secure environment variable handling
- **Health Checks**: Built-in health monitoring endpoints

## 🏗️ System Architecture


![Image](https://github.com/mikedevcypher/Taskflow-manager/blob/main/assets/task-manager-architectural-diagram.png)


## 🛠️ Technology Stack

### Backend
- **Framework**: Flask 2.3+ with Flask-RESTful
- **Database**: PostgreSQL 13+ (Production) / SQLite (Development)
- **Cache**: Redis 6+ for session management and data caching
- **Authentication**: JWT with Flask-JWT-Extended, OAuth2 support
- **ORM**: SQLAlchemy with Alembic migrations
- **Task Queue**: Celery for background job processing

### Frontend
- **Framework**: React 18+ with TypeScript
- **Styling**: Tailwind CSS for responsive design
- **State Management**: Redux Toolkit for state management
- **HTTP Client**: Axios for API communication
- **Build Tool**: Vite for fast development and building

### DevOps & Deployment
- **Containerization**: Docker & Docker Compose
- **Cloud Platform**: AWS (EC2, RDS, ElastiCache, S3)
- **Web Server**: Nginx (Production reverse proxy)
- **Process Manager**: Gunicorn for production WSGI
- **Monitoring**: Health check endpoints and logging

### Development Tools
- **API Documentation**: Swagger/OpenAPI 3.0
- **Code Quality**: Black, flake8, mypy for code standards
- **Environment Management**: python-dotenv for configuration

## 📁 Project Structure

```
taskflow-manager/
├── assets/                      # Static assets
├── config/                      # Configuration files
│   ├── __init__.py
│   ├── config.py               # Application configuration
│   └── settings.py             # Environment-specific settings
├── src/
│   ├── static/
│   │   └── swagger.json        # API documentation
│   ├── task_management/        # Core application
│   │   ├── auth/              # Authentication module
│   │   │   ├── __init__.py
│   │   │   ├── models.py      # User models
│   │   │   ├── routes.py      # Auth endpoints
│   │   │   └── security.py    # Security implementations
│   │   ├── tasks/             # Task management module
│   │   │   ├── __init__.py
│   │   │   ├── models.py      # Task models
│   │   │   └── routes.py      # Task endpoints
│   │   ├── categories/        # Category management
│   │   │   ├── __init__.py
│   │   │   ├── models.py      # Category models
│   │   │   └── routes.py      # Category endpoints
│   │   ├── integrations/      # Third-party integrations
│   │   │   ├── __init__.py
│   │   │   └── slack.py       # Slack integration
│   │   ├── cache/             # Caching layer
│   │   │   ├── __init__.py
│   │   │   └── redis_client.py # Redis implementation
│   │   ├── __init__.py
│   │   └── db.py              # Database configuration
│   ├── templates/             # HTML templates
│   └── main.py                # Application entry point
├── docker/                    # Docker configurations
├── .dockerignore
├── .env                    # Environment variables template
├── .gitignore
├── docker-compose.yml        # Development container setup
├── Dockerfile                # Container definition
├── requirements.txt          # Python dependencies
└── README.md                 # ReadMe.md
```

## 🚀 Quick Start

### Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.10+**: [Download Python](https://www.python.org/downloads/)
- **Docker**: [Install Docker](https://docs.docker.com/get-docker/)
- **Docker Compose**: [Install Docker Compose](https://docs.docker.com/compose/install/)
- **Git**: [Install Git](https://git-scm.com/downloads)

### Local Development Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/mikedevcypher/Taskflow-manager.git
   cd Taskflow-manager
   ```

2. **Environment Configuration**
   ```bash
   # Copy environment template
   cp .env.example .env
   
   # Edit the .env file with your configuration
   nano .env
   ```

3. **Environment Variables Setup**
   ```bash
   # Database Configuration
   DATABASE_URL=postgresql://username:password@localhost:5432/taskflow
   
   # Redis Configuration
   REDIS_URL=redis://localhost:6379/0
   
   # JWT Configuration
   JWT_SECRET_KEY=your-super-secret-jwt-key
   JWT_ACCESS_TOKEN_EXPIRES=86400
   
   
   # Slack Integration (Optional)
   SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
   SLACK_SIGNING_SECRET=your-slack-signing-secret
   
   # Email Configuration
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-app-password
   ```

4. **Docker Development Setup**
   ```bash
   # Build and start all services
   docker-compose up --build
   
   # Run database migrations
   docker-compose exec web flask db migrate -m "Initial migration"
   docker-compose exec web flask db upgrade
   ```

5. **Access the Application**
   - **Web Application**: http://localhost:5000
   - **API Documentation**: http://localhost:5000/api/docs
   - **Health Check**: http://localhost:5000/health

### Manual Setup (Alternative)

If you prefer to set up without Docker:

1. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # For development
   ```

3. **Database Setup**
   ```bash
   # Initialize database
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

4. **Run the Application**
   ```bash
   flask run --debug
   ```

## 🐳 Docker Deployment

### Development Environment

```bash
# Start development environment
docker-compose up --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```



## ☁️ Cloud Deployment Guide

### AWS Deployment

#### Prerequisites
- AWS CLI configured with appropriate permissions
- Terraform (optional, for infrastructure as code)
- Domain name for SSL certificate

#### 1. Infrastructure Setup

**EC2 Instance Setup:**
```bash
# Launch EC2 instance 
# Install Docker and Docker Compose
sudo yum update -y
sudo yum install -y docker
sudo service docker start
sudo usermod -a -G docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

**RDS PostgreSQL Setup:**
```bash
# Create RDS instance via AWS Console or CLI
aws rds create-db-instance \
    --db-instance-identifier taskflow-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --master-username taskflow_admin \
    --master-user-password YourSecurePassword123! \
    --allocated-storage 20 \
    --vpc-security-group-ids sg-xxxxxxxxx \
    --db-subnet-group-name default
```

**ElastiCache Redis Setup:**
```bash
# Create Redis cluster
aws elasticache create-cache-cluster \
    --cache-cluster-id taskflow-redis \
    --cache-node-type cache.t3.micro \
    --engine redis \
    --num-cache-nodes 1
```

#### 2. Application Deployment

**Production Environment File:**
```bash
# Create production .env file
cat > .env.prod << EOF
# Production Environment
FLASK_ENV=production
SECRET_KEY=$(openssl rand -hex 32)

# Database (Update with your RDS endpoint)
DATABASE_URL=postgresql://taskflow_admin:YourSecurePassword123!@taskflow-db.xxxxxxxxx.us-east-1.rds.amazonaws.com:5432/taskflow

# Redis (Update with your ElastiCache endpoint)
REDIS_URL=redis://taskflow-redis.xxxxxx.cache.amazonaws.com:6379/0

# JWT Configuration
JWT_SECRET_KEY=$(openssl rand -hex 32)
JWT_ACCESS_TOKEN_EXPIRES=86400

# SSL and Security
FORCE_HTTPS=true
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true

# Email Configuration
MAIL_SERVER=smtp.amazonaws.com
MAIL_PORT=587
MAIL_USERNAME=your-ses-smtp-username
MAIL_PASSWORD=your-ses-smtp-password
EOF
```



#### 3. Load Balancer Configuration

**Application Load Balancer Setup:**
```bash
# Create target group
aws elbv2 create-target-group \
    --name taskflow-targets \
    --protocol HTTP \
    --port 5000 \
    --vpc-id vpc-xxxxxxxxx \
    --health-check-path /health

# Create load balancer
aws elbv2 create-load-balancer \
    --name taskflow-alb \
    --subnets subnet-xxxxxxxxx subnet-yyyyyyyyy \
    --security-groups sg-xxxxxxxxx
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `FLASK_ENV` | Flask environment | `development` | No |
| `SECRET_KEY` | Flask secret key | Generated | Yes |
| `DATABASE_URL` | PostgreSQL connection string | SQLite file | No |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` | No |
| `JWT_SECRET_KEY` | JWT signing key | Generated | Yes |
| `JWT_ACCESS_TOKEN_EXPIRES` | Token expiry (seconds) | `86400` | No |
| `SLACK_BOT_TOKEN` | Slack bot token | None | No |
| `SLACK_SIGNING_SECRET` | Slack signing secret | None | No |
| `MAIL_SERVER` | SMTP server | None | No |
| `MAIL_PORT` | SMTP port | `587` | No |
| `MAIL_USERNAME` | SMTP username | None | No |
| `MAIL_PASSWORD` | SMTP password | None | No |

### Database Configuration

**PostgreSQL Production Setup:**
```sql
-- Create database
CREATE DATABASE taskflow;

-- Create user
CREATE USER taskflow_user WITH PASSWORD 'secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE taskflow TO taskflow_user;

-- Enable required extensions
\c taskflow
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
```


## 📊 API Documentation

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | User login |
| POST | `/api/auth/logout` | User logout |
| POST | `/api/auth/refresh` | Refresh JWT token |
| GET | `/api/auth/me` | Get current user info |

### Task Management Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tasks` | List all user tasks |
| POST | `/api/tasks` | Create new task |
| GET | `/api/tasks/{id}` | Get specific task |
| PUT | `/api/tasks/{id}` | Update task |
| DELETE | `/api/tasks/{id}` | Delete task |
| PATCH | `/api/tasks/{id}/status` | Update task status |

### Category Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/categories` | List categories |
| POST | `/api/categories` | Create category |
| PUT | `/api/categories/{id}` | Update category |
| DELETE | `/api/categories/{id}` | Delete category |

### Dashboard & Analytics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard` | Dashboard statistics |
| 

### Example API Usage

**Create a New Task:**
```bash
curl -X POST "http://localhost:5000/api/tasks" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Complete project documentation",
    "description": "Write comprehensive README and API docs",
    "priority": "high",
    "due_date": "2024-12-31T23:59:59Z",
    "category_id": 1
  }'
```

**Get User Tasks:**
```bash
curl -X GET "http://localhost:5000/api/tasks?status=pending&priority=high" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 🧪 Testing

### Running Tests

**All Tests:**
```bash
# Using Docker
docker-compose exec web python -m pytest

# Local environment
python -m pytest
```


## 🔒 Security Features

### Authentication & Authorization
- **JWT-based Authentication**: Stateless authentication with configurable expiry
- **Password Security**: Bcrypt hashing with salt
- **OAuth2 Integration**: Google, GitHub, and custom OAuth providers
- **Role-based Access Control**: Fine-grained permissions system
- **Session Management**: Secure session handling with Redis

### API Security
- **Rate Limiting**: Configurable rate limits per endpoint
- **CORS Protection**: Cross-origin request security
- **Input Validation**: Comprehensive input sanitization
- **SQL Injection Prevention**: SQLAlchemy ORM protection
- **XSS Protection**: Content Security Policy headers

### Data Protection
- **Data Encryption**: Sensitive data encryption at rest
- **HTTPS Enforcement**: SSL/TLS for all communications
- **Secure Headers**: Security headers implementation
- **Environment Isolation**: Secure environment variable handling

## 📈 Performance Optimization

### Caching Strategy
- **Redis Caching**: Multi-level caching implementation
- **Database Query Optimization**: Strategic indexing
- **API Response Caching**: Cached responses for read-heavy operations
- **Session Storage**: Redis-based session management

### Database Optimization
```sql
-- Essential indexes for performance
CREATE INDEX idx_tasks_user_id ON tasks(user_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_due_date ON tasks(due_date);
CREATE INDEX idx_tasks_priority ON tasks(priority);
CREATE INDEX idx_task_assignments_user_id ON task_assignments(user_id);
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
```

### Monitoring & Logging
- **Application Metrics**: Performance monitoring
- **Error Tracking**: Comprehensive error logging
- **Health Checks**: System health monitoring endpoints
- **Log Aggregation**: Centralized logging system

## 🔗 Integration Guide

### Slack Integration

**Setup Slack App:**
1. Create a new Slack app at https://api.slack.com/apps
2. Add OAuth scopes: `chat:write`, `commands`, `im:read`
3. Install app to workspace
4. Copy bot token and signing secret to environment variables

**Available Slack Commands:**
```bash
# Create task from Slack
/task create "Review pull request" priority:high due:tomorrow

# List tasks
/task list status:pending

# Update task status
/task complete 123
```

### Email Notifications

**Supported Email Providers:**
- SMTP (Gmail, Outlook, etc.)
- Amazon SES
- SendGrid
- Mailgun

**Notification Types:**
- Task assignment notifications
- Due date reminders
- Task completion alerts
- Weekly task summaries

## 🛠️ Development

### Code Standards
- **PEP 8**: Python code style guidelines
- **Black**: Code formatting
- **flake8**: Linting and style checking
- **mypy**: Static type checking
- **isort**: Import statement sorting

### Git Workflow
```bash
# Feature development
git checkout -b feature/new-feature
git commit -m "feat: add new feature"
git push origin feature/new-feature

# Create pull request
# After review and approval, merge to main
```

### Database Migrations
```bash
# Create migration
flask db migrate -m "Add new table"

# Apply migration
flask db upgrade

# Rollback migration
flask db downgrade
```

## 🚨 Troubleshooting

### Common Issues

**Database Connection Issues:**
```bash
# Check database connectivity
docker-compose exec web flask db-check

# Reset database
docker-compose exec web flask db-reset
```

**Redis Connection Issues:**
```bash
# Test Redis connection
docker-compose exec redis redis-cli ping

# Clear Redis cache
docker-compose exec redis redis-cli flushall
```

**Permission Issues:**
```bash
# Fix file permissions
sudo chown -R $USER:$USER .
chmod +x scripts/*.sh
```

### Logs and Debugging
```bash
# View application logs
docker-compose logs -f web

# View database logs
docker-compose logs -f db

# Enable debug mode
export FLASK_ENV=development
export FLASK_DEBUG=1
```

## 📋 Production Checklist

### Pre-deployment
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] SSL certificate installed
- [ ] Security headers configured
- [ ] Rate limiting enabled
- [ ] Monitoring setup complete
- [ ] Backup strategy implemented
- [ ] Load testing completed

### Post-deployment
- [ ] Health checks passing
- [ ] Logs monitoring active
- [ ] Performance metrics baseline
- [ ] Security scan completed
- [ ] User acceptance testing
- [ ] Documentation updated
- [ ] Team training completed

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

### Code Review Process
- All changes require peer review
- Tests must pass
- Code coverage must be maintained
- Documentation must be updated

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Getting Help
- **Documentation**: Check this README and `/docs` folder
- **Issues**: [GitHub Issues](https://github.com/mikedevcypher/Taskflow-manager/issues)
- **Discussions**: [GitHub Discussions](https://github.com/mikedevcypher/Taskflow-manager/discussions)



---

**Built with ❤️ by [Mike DevCypher](https://github.com/mikedevcypher)**

