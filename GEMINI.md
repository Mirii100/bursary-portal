# 🎓 Project Title: Alexia's Global Tech Constituency Bursary System (ATCBS)

## 1️⃣ Background Problem
Currently, bursary allocation is manual, leading to:
- Lost documents, double allocation, ghost beneficiaries, slow processing, and lack of accountability.

## 2️⃣ Project Goal
Develop a secure web-based bursary management system using Django for online application, digital review, and transparent fund tracking.

## 3️⃣ Project Objectives
- **Main Objective**: Design and implement a secure, transparent, and efficient online bursary application and management system.
- **Specific Objectives**:
    - Online student registration and applications.
    - Document uploads (fee structure, admission letter, ID, etc.).
    - Administrator review, approval, and rejection workflows.
    - Automated eligibility checks and duplicate detection.
    - Report generation for leadership.
    - Audit logs and SMS/Email notifications.
    - Centralized digital database.

## 4️⃣ System Users (Roles)
- **Student**: Register, Apply, Upload, Track.
- **Bursary Committee Member**: Review, Score, Recommend.
- **Admin (MP Office Staff)**: Manage users, Finalize allocations, Budgeting, Reporting.
- **Super Admin**: Full system control, Security, Logs.

## 5️⃣ Technical Stack
- **Backend**: Django, Django REST Framework.
- **Frontend**: HTML, CSS (Vanilla/Bootstrap), JavaScript.
- **Database**: PostgreSQL (Production), SQLite (Development).
- **Deployment**: Nginx, Gunicorn, Ubuntu.
- **Integrations**: SMS API, M-Pesa API, Email.

## 6️⃣ Core Modules
1. User Management (RBAC)
2. Application Module (Forms + Uploads)
3. Review & Approval (Scoring)
4. Disbursement Tracking
5. Reporting & Analytics
6. Audit & Transparency

## 7️⃣ Database Models (Planned)
- `User`, `StudentProfile`, `Application`, `Documents`, `Payment`, `AuditLog`.

## 8️⃣ Security
- HTTPS, RBAC, Encryption, Validation, 2FA, Activity Logging.

---

## 🚀 Development Progress

- [x] Project Initialization
- [x] Django Project Setup
- [x] Core Database Models Implementation (with Smart Validation)
- [x] Admin Panel Configuration
- [x] Basic Landing Page (Home)
- [x] User Authentication (Student Registration/Login)
- [x] Student Profile Creation
- [x] Application Submission Workflow (with Mandatory Docs)
- [x] Document Upload Integration (ID, Fee Structure)
- [x] Committee Review Dashboard & Scoring System
- [x] MP Office Admin Dashboard
- [x] Reporting & Audit Logs (Export to PDF/Excel)
- [x] SMS/Email Integration
- [x] Payment Tracking (M-Pesa/Bank Integration)
