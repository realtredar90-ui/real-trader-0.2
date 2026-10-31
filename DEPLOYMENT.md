# Deployment checklist

1. Upload the complete project with the folder structure preserved.
2. Set `SECRET_KEY` to a unique random value in the hosting provider's environment settings.
3. Set `COOKIE_SECURE=1` when HTTPS is enabled.
4. Configure persistent storage and set `DATABASE_PATH` to a location on that storage.
5. Install dependencies from `requirements.txt`.
6. Start with the Procfile command: `gunicorn app:app`.
7. Verify registration, login, add trade, journal, reports and logout.
8. Configure backups and review privacy/security before real users use the app.

Do not store broker passwords, API keys, payment details, or other sensitive credentials in this starter project. This project is not a security-audited production service.
