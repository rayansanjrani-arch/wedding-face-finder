# Security Model

## Authentication

- Session-based with Flask-Login
- bcrypt password hashing
- Rate limiting: 5 attempts per minute on login

## Authorization

- Admin routes protected by `@login_required`
- Event isolation: users can only access their event data

## Data Protection

- Photos encrypted at rest using Fernet (AES-128-CBC)
- Auto-purge: 30 days or on-demand
- Audit logs: every search, upload, and purge tracked

## Headers

- Content-Security-Policy via Flask-Talisman
- HSTS, X-Frame-Options, X-Content-Type-Options