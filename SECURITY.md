# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| `main`  | ✅        |

## Threat Model

| Threat | Mitigation |
|--------|------------|
| Path traversal | UUID-based filenames; `validators.py` rejects `../` |
| SQL Injection | SQLAlchemy ORM with parameterized queries |
| XSS | Jinja2 auto-escaping; CSP + security headers via Flask `after_request` |
| CSRF | Flask-WTF tokens on all forms; API blueprints exempted for stateless endpoints |
| Brute force | Flask-Limiter (`login_rate_limit` default: 5/min) |
| Session hijacking | `HttpOnly`, `Secure`, `SameSite=Lax` cookies |
| Data exposure | Optional face-encoding encryption (`encryption_key`); manual purge via admin API |
| File upload abuse | Magic bytes + MIME + `max_content_length` validation |

## Reporting

If you discover a vulnerability, please email:

**rayansanjrani@gmail.com**

Please include:
- Description
- Steps to reproduce
- Impact assessment
- Suggested fix (optional)

We aim to respond within 48 hours.