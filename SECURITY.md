# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| main    | ✅ |

## Threat Model

| Threat | Mitigation |
|--------|-----------|
| Path traversal | UUID-based storage, validators.py rejects `../` |
| SQL Injection | SQLAlchemy ORM, parameterized queries |
| XSS | Jinja2 auto-escaping, CSP headers via Talisman |
| CSRF | Flask-WTF tokens on all forms |
| Brute force | Flask-Limiter (5/min on login) |
| Data exposure | AES-256 encryption, auto-purge after 30 days |
| File upload abuse | Magic bytes + MIME + size validation |

## Reporting

Email: security@yourdomain.com

Please include:
- Description
- Steps to reproduce
- Impact assessment
- Suggested fix (optional)

We respond within 48 hours.