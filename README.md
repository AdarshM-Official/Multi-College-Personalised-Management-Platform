# Multi-College Personalised Management Platform (SaaS)

A production-ready, multi-tenant SaaS platform built with Django for managing colleges and educational institutions. This platform allows multiple independent colleges to onboard, manage their internal operations (students, teachers, HODs), and maintain their personalized portal securely within a single unified application.

## 🌟 Key Features

### 🏢 True Multi-Tenancy
- **Isolated Data:** Each college's data is securely isolated using a `college_id` foreign key.
- **Custom Branding:** Institutions can upload their own logo, configure a custom theme color, and build a campus gallery.
- **Dynamic Routing:** Subdomain support (e.g., `http://{college-slug}.localhost:8000`) for personalized access.

### 🔐 Robust Role-Based Access Control (RBAC)
Custom User models with email-based authentication and 5 distinct roles:
1. **Super Admin:** Global system administrator who approves/rejects new college registrations.
2. **College Admin:** Local administrator for a specific college who manages HODs, Teachers, and Students.
3. **Head of Department (HOD):** Manages a specific department within a college.
4. **Teacher:** Manages classes, attendance, and assignments.
5. **Student:** Views classes, submits assignments, and checks attendance.

### 🏫 College Onboarding & Verification
- Dedicated registration flow for new institutions.
- Secure upload of verification documents and registration numbers.
- Automated approval/rejection workflows managed by Super Admins.
- Rejection feedback loop for institutions to correct their details.

### 📚 Academic Management (Core & Management Modules)
- **Attendance System:** Daily attendance tracking by teachers.
- **Assignment System:** Upload assignments and track student submissions.
- **Department Management:** Organized structure linking HODs, Teachers, and Students.

## 🛠️ Technology Stack

- **Backend:** Python 3.10+, Django, Django REST Framework
- **Database:** SQLite (Local Dev) / PostgreSQL (Production ready)
- **Frontend:** HTML5, CSS3, Bootstrap 5, JavaScript
- **Data Handling:** Pandas, OpenPyXL (for Excel/CSV imports/exports)
- **Media Processing:** Pillow (for image optimization)

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10 or higher
- Git
- PostgreSQL (Recommended for production)

### 2. Installation Setup
```bash
# Clone the repository
git clone <your-repo-url>
cd collegevendor

# Create and activate a virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

### 3. Database & Migrations
```bash
# Run migrations to set up the database schema
python manage.py makemigrations
python manage.py migrate
```

### 4. Create Global Super Admin
```bash
python manage.py createsuperuser
# Enter email, and password as prompted
```

### 5. Run the Development Server
```bash
python manage.py runserver
```
Visit `http://localhost:8000` to access the platform.

## 🧪 Testing the Workflow (Local Dev)

1. **Register a College:** Go to the homepage and register a new institution.
2. **Approve the College:** Log in as the Super Admin (at `/admin` or Super Admin Dashboard) and approve the pending college registration.
3. **College Setup:** Log in with the newly created College Admin credentials.
4. **Onboard Staff & Students:** Navigate to the College Admin dashboard to add Departments, HODs, Teachers, and Students.
5. **Academic Flow:** Log in as a Teacher to post an assignment, then log in as a Student to view and submit it.

## 🔐 Environment Variables

Create a `.env` file in the project root for production setups:
```env
DEBUG=True
SECRET_KEY=your-django-secure-secret-key
DATABASE_URL=postgres://user:password@localhost:5432/college_db
CLOUDINARY_URL=cloudinary://api_key:api_secret@cloud_name # (Optional: For cloud media storage)
```

## 🏗️ Project Structure
```text
collegevendor/
├── accounts/           # Custom User Model and Auth workflows
├── colleges/           # College registration, verification, and settings
├── core/               # Main website, landing pages, and global views
├── management/         # Academic logic: Attendance, assignments, departments
├── templates/          # Global HTML templates (Dashboards, Base layouts)
├── media/              # User-uploaded files (Logos, Docs, Assignments)
└── static/             # CSS, JS, and image assets
```

## 🛡️ Security Best Practices Implemented
- **Tenant Isolation Context:** Middleware and querysets ensure `request.user.college` is strictly enforced to prevent data leakage between tenants.
- **Secure Password Hashing:** Powered by Django's native cryptographic hashers.
- **CSRF Protection:** Enforced across all state-changing endpoints and forms.
- **Role Validation:** Custom decorators (`@login_required`, role checks) prevent unauthorized access to specific dashboard views.
