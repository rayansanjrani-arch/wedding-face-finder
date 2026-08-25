# Changelog

## [1.0.0] — 2026-08-26

### Added
- Flask app factory with security headers
- SQLAlchemy models + Alembic migrations
- Face engine: CNN→HOG cascade with blur detection
- REST API: upload, search, download, admin
- Mobile-first frontend with drag-drop + camera
- Admin dashboard with stats and audit logs
- Docker + docker-compose setup
- GitHub Actions CI/CD pipeline
- Full documentation suite

### Security
- Talisman CSP headers
- Rate limiting on all sensitive endpoints
- bcrypt password hashing
- Fernet encryption for face encodings