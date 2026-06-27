# SecurePass Analyzer

**Analyze • Improve • Secure**

A professional, enterprise‑grade web application for password strength analysis, generation, and cybersecurity education.

## Features
- Landing Page with animations, dark/light mode
- User Authentication (signup, login, profile)
- Password Strength Analyzer (entropy, crack time, recommendations)
- Secure Password Generator (cryptographically secure)
- Password History (hashed storage, search, pagination)
- Analytics Dashboard with charts (trends, distribution)
- Cybersecurity Learning Center
- PDF Report Generation
- REST API (analyze, generate, history, dashboard, report)
- Admin Panel (user management, logs, system stats)

## Quick Start
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your SECRET_KEY
flask run