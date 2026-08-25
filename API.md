# API Reference

Base URL: `http://127.0.0.1:5000`

---

## Authentication

### POST /api/admin/login

```bash
curl -X POST http://127.0.0.1:5000/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"yourpassword"}'