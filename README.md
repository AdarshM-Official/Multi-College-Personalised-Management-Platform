# Multi-College Management SaaS Platform (Django)

A production-ready multi-tenant SaaS platform for college management.

## Features
- **Multi-tenancy**: Isolated data per college using `college_id`.
- **RBAC**: Super Admin, College Admin, Teacher, Student roles.
- **Attendance**: Daily attendance marking by teachers.
- **Assignments**: Upload and submission system for students and teachers.
- **Personalization**: Dynamic themes and logos for each college portal.
- **Responsive UI**: Built with Bootstrap 5.

## Installation

### 1. Prerequisite
- Python 3.10+
- PostgreSQL (recommended) or SQLite (for local dev)

### 2. Setup
```bash
# Clone the repository
git clone <repo-url>
cd college-manager-saas

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install django psycopg2-binary pillow django-rest-framework
```

### 3. Database Migrations
```bash
python manage.py makemigrations accounts colleges management
python manage.py migrate
```

### 4. Create Super Admin (Global)
```bash
python manage.py createsuperuser
```

### 5. Run Server
```bash
python manage.py runserver
```

## Environment Variables (.env)
```env
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgres://user:password@localhost:5432/college_db
CLOUDINARY_URL=cloudinary://api_key:api_secret@cloud_name (Optional for file uploads)
```

## Testing Instructions
1. Register a new college at `/register/`.
2. This creates a College Admin account.
3. Log in as College Admin.
4. Go to Dashboard -> Manage Students -> Add Student.
5. Create a Teacher account.
6. Log in as Teacher to post assignments or mark attendance.
7. Log in as Student to see assignments and submission details.

## Deployment Steps (Render/Heroku/Vercel)
1. Set up a PostgreSQL database.
2. Configure `ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS`.
3. Use `gunicorn` for serving the application.
4. Set up static files collection: `python manage.py collectstatic`.
5. For file uploads in production, use AWS S3 or Cloudinary.

## Security Best Practices
- **Isolation**: Middleware ensures `request.college` is always set and used for filtering.
- **Hashing**: Django handles secure password hashing automatically.
- **CSRF**: All POST forms include `{% csrf_token %}`.
- **RBAC**: Decorators like `@login_required` and role checks protect sensitive views.
