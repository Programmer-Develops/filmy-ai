# Setting up environment variables for Filmy AI

Do NOT commit secrets into the repository. Create a local `.env` file (gitignored) or set environment variables in your system.

1) Create a local `.env` from the example

Windows PowerShell:

```powershell
Copy-Item .env.example .env
(Get-Content .env) -replace 'replace_with_your_gemini_api_key','YOUR_REAL_KEY_HERE' | Set-Content .env -Encoding UTF8
# Or manually edit .env with a text editor and paste your key.
```

Alternatively, create `.env` directly:

```powershell
Set-Content -Path .env -Value 'GEMINI_API_KEY=YOUR_REAL_KEY_HERE' -Encoding UTF8
```

Linux / macOS:

```bash
cp .env.example .env
sed -i "s/replace_with_your_gemini_api_key/YOUR_REAL_KEY_HERE/" .env
# or
echo "GEMINI_API_KEY=YOUR_REAL_KEY_HERE" > .env
```

2) Or set system environment variable (PowerShell, affects current user):

```powershell
setx GEMINI_API_KEY "YOUR_REAL_KEY_HERE"
```

3) Verify the app reads `.env` (the app uses Pydantic BaseSettings and will load `.env` automatically as configured in `app/config.py`).

4) For production, prefer storing secrets in a secret manager (e.g., Google Secret Manager) and do NOT store them in plain text files in the repo.
