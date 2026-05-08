# CSE722 Project 2 — WebAuthn Passwordless Authentication
 
![WebAuthn](https://img.shields.io/badge/WebAuthn-FIDO2-blue)
![Python](https://img.shields.io/badge/Python-3.11%2B-green)
![Flask](https://img.shields.io/badge/Flask-3.0%2B-lightgrey)
![Windows](https://img.shields.io/badge/OS-Windows%2010%2F11-0078D6)
 
A full-stack **passwordless authentication web-service** built using the **WebAuthn (FIDO2)** framework for CSE722: Security Engineering. Users can register a passkey on one device and authenticate from multiple browsers across multiple devices — no password required.
 
> 🖥️ This guide is written for **Windows 10 / Windows 11** only.
 
---
 
## 📋 Table of Contents
 
- [Features](#features)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Generate TLS Certificate](#generate-tls-certificate)
- [Running the Server — Desktop Mode](#running-the-server--desktop-mode)
- [Desktop Browser Testing](#desktop-browser-testing)
- [Running the Server — Mobile Mode](#running-the-server--mobile-mode)
- [Mobile Browser Testing](#mobile-browser-testing)
- [API Endpoints](#api-endpoints)
- [WebAuthn Flow](#webauthn-flow)
- [Server Verification Steps](#server-verification-steps)
- [Negative Tests](#negative-tests)
- [Environment Variables](#environment-variables)
- [Troubleshooting](#troubleshooting)
- [References](#references)
---
 
## ✨ Features
 
- ✅ Full WebAuthn **Registration (Attestation)** ceremony
- ✅ Full WebAuthn **Authentication (Assertion)** ceremony
- ✅ HTTPS with self-signed certificate for desktop testing
- ✅ Mobile testing via **Cloudflare Tunnel** (free, no account needed)
- ✅ Support for **Windows Hello (PIN)**, **Android biometrics**, **Google Password Manager**
- ✅ Protected page showing username and full authenticator information
- ✅ **Signature counter** tracking and cloned-authenticator detection
- ✅ Server verifies **challenge, origin, RP ID hash, UP/UV flags, signature**
- ✅ Negative tests: rejects unregistered users, tampered signatures, foreign credentials
- ✅ Cross-device credential usage via environment variable RP configuration (Bonus)
---
 
## 📁 Project Structure
 
```
webauthn-project/
├── server/
│   ├── app.py              ← Flask server (all WebAuthn logic)
│   └── requirements.txt    ← Python dependencies
├── client/
│   └── index.html          ← Frontend single-page application
├── certs/
│   ├── cert.pem            ← TLS certificate (you generate this)
│   └── key.pem             ← TLS private key (you generate this)
├── README.md               ← This file
└── .gitignore
```
 
---
 
## 🔧 Prerequisites
 
Install the following software before starting:
 
### 1 — Python 3.11 or 3.12
 
- Download from: https://python.org/downloads
- During installation — ✅ check **"Add Python to PATH"**
- Verify:
```cmd
python --version
pip --version
```
 
### 2 — Git for Windows (includes OpenSSL)
 
- Download from: https://git-scm.com/download/win
- Install with all **default settings**
- Verify:
```cmd
git --version
openssl version
```
 
### 3 — cloudflared.exe (for mobile testing only)
 
- Download from:
```
https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe
```
- Create folder:
```cmd
mkdir C:\cloudflared
```
- Move the downloaded file to `C:\cloudflared\` and rename it to `cloudflared.exe`
- Verify:
```cmd
C:\cloudflared\cloudflared.exe --version
```
 
---
 
## 🚀 Installation
 
### Step 1 — Extract the Project
 
Unzip the project to your Desktop:
```
C:\Users\YourName\Desktop\webauthn-project\
```
 
### Step 2 — Open Command Prompt in Project Folder
 
Press `Win + R` → type `cmd` → Enter, then:
```cmd
cd "C:\Users\YourName\Desktop\webauthn-project\webauthn-project"
```
 
### Step 3 — Create Virtual Environment
 
```cmd
python -m venv venv
venv\Scripts\activate
```
 
You will see `(venv)` in your prompt.
 
### Step 4 — Install Python Dependencies
 
```cmd
pip install flask flask-session webauthn==2.7.1 cbor2 cryptography
```
 
Verify correct version:
```cmd
python -c "import webauthn; print(webauthn.__version__)"
```
 
Must output: `2.7.1`
 
> ⚠️ Do NOT install `py-webauthn` or `py_webauthn` — the correct package name is just `webauthn==2.7.1`
 
---
 
## 🔐 Generate TLS Certificate
 
WebAuthn requires HTTPS. Generate a self-signed TLS certificate before running the server.
 
### Open Git Bash
 
Right-click on your Desktop → click **"Git Bash Here"**
 
### Run This Command
 
```bash
cd ~/Desktop/webauthn-project/webauthn-project
mkdir -p certs
 
openssl req -x509 -newkey rsa:4096 \
  -keyout certs/key.pem \
  -out certs/cert.pem \
  -days 365 -nodes \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
```
 
### Answer the Prompts
 
```
Country Name (2 letter code): BD
State or Province Name: Dhaka
Locality Name: Dhaka
Organization Name: CSE722
Organizational Unit Name: WebAuthn
Common Name: localhost
Email Address: (press Enter to skip)
```
 
### Verify Both Files Were Created
 
```bash
ls certs/
```
 
Must show: `cert.pem  key.pem`
 
---
 
## ▶️ Running the Server — Desktop Mode
 
Use this mode for testing on your PC with Chrome, Edge, and Firefox.
 
### Open Command Prompt
 
```cmd
cd "C:\Users\YourName\Desktop\webauthn-project\webauthn-project\server"
call ..\venv\Scripts\activate
```
 
### Start the Server
 
```cmd
set TLS_CERT=..\certs\cert.pem
set TLS_KEY=..\certs\key.pem
set RP_ID=localhost
set ORIGIN=https://localhost:5000
python app.py
```
 
### Expected Output
 
```
[+] Starting HTTPS server on port 5000
[+] RP_ID=localhost  ORIGIN=https://localhost:5000
 * Running on https://127.0.0.1:5000
```
 
### Open in Browser
 
```
https://localhost:5000
```
 
> ⚠️ The browser shows a security warning for self-signed certificates — this is normal.
> - **Chrome / Edge:** Click **Advanced** → **Proceed to localhost (unsafe)**
> - **Firefox:** Click **Advanced** → **Accept the Risk and Continue**
 
---
 
## 🖥️ Desktop Browser Testing
 
Test on all three browsers at `https://localhost:5000`.
 
### Register a Passkey
 
1. Type a username (e.g. `alice`)
2. Click **Register Passkey**
3. **Windows Hello PIN prompt** appears → enter your Windows PIN
4. Success message: `✅ Passkey registered!`
### Sign In with Passkey
 
1. Click the **Sign In** tab
2. Type the same username
3. Click **Sign In with Passkey**
4. **Windows Hello PIN** → enter PIN
5. Protected dashboard appears ✅
### Desktop Test Summary
 
| Browser | Certificate Action | Authenticator | Expected Result |
|---|---|---|---|
| Chrome | Advanced → Proceed to localhost | Windows Hello PIN | ✅ Pass |
| Edge | Advanced → Continue | Windows Hello PIN | ✅ Pass |
| Firefox | Advanced → Accept the Risk | Windows Hello PIN | ✅ Pass |
 
> 💡 Use different usernames per browser (e.g. `alice`, `alice_edge`, `alice_firefox`)
 
---
 
## 📱 Running the Server — Mobile Mode
 
Use this mode for testing from Android/iOS phones.
 
### Why Cloudflare Tunnel?
 
WebAuthn blocks on non-HTTPS URLs from external devices. Cloudflare Tunnel provides a free public HTTPS URL for your local server automatically.
 
> ⚠️ Do NOT use ngrok free tier — ngrok free domains (`.ngrok-free.dev`) are blocked by WebAuthn browsers.
 
### Step 1 — Open Terminal 1 — Start Server in HTTP Mode
 
```cmd
cd "C:\Users\YourName\Desktop\webauthn-project\webauthn-project\server"
call ..\venv\Scripts\activate
set TLS_CERT=notexist
set TLS_KEY=notexist
set RP_ID=PLACEHOLDER
set ORIGIN=PLACEHOLDER
python app.py
```
 
Server must show:
```
[!] TLS certificate not found – falling back to HTTP
 * Running on http://127.0.0.1:5000
```
 
### Step 2 — Open Terminal 2 — Start Cloudflare Tunnel
 
Open a **new Command Prompt** window:
```cmd
C:\cloudflared\cloudflared.exe tunnel --url http://localhost:5000
```
 
Wait 15 seconds. You will see:
```
+----------------------------------------------------------+
| Your quick Tunnel has been created! Visit it at:         |
| https://abc-def-123-xyz.trycloudflare.com                |
+----------------------------------------------------------+
```
 
**Copy the full domain** — example: `abc-def-123-xyz.trycloudflare.com`
 
### Step 3 — Stop Server (Ctrl+C) and Restart with Tunnel Domain
 
```cmd
set TLS_CERT=notexist
set TLS_KEY=notexist
set RP_ID=abc-def-123-xyz.trycloudflare.com
set ORIGIN=https://abc-def-123-xyz.trycloudflare.com
python app.py
```
 
Replace `abc-def-123-xyz.trycloudflare.com` with your actual tunnel domain.
 
### Step 4 — Verify on PC First
 
Open Chrome on your PC and go to the tunnel URL — the WebAuthn page should load correctly.
 
---
 
## 📱 Mobile Browser Testing
 
### Install 3 Browsers on Android Phone
 
| Browser | Download |
|---|---|
| Chrome | Pre-installed on most Android phones |
| Firefox | Play Store → search "Firefox" |
| Microsoft Edge | Play Store → search "Microsoft Edge" |
 
### Open Each Browser on Phone
 
Go to tunnel URL on each browser:
```
https://abc-def-123-xyz.trycloudflare.com
```
 
### Register on Mobile
 
1. Type a username (e.g. `mobile_chrome`)
2. Tap **Register Passkey**
3. Phone asks for **fingerprint or PIN** → authenticate
4. Success ✅
### Sign In on Mobile
 
1. Tap **Sign In** tab
2. Type same username
3. Tap **Sign In with Passkey**
4. Fingerprint/PIN → Protected dashboard ✅
### Mobile Test Summary
 
| Browser | Username | Authenticator | Expected Result |
|---|---|---|---|
| Chrome Mobile | `mobile_chrome` | iOS PIN / Fingerprint | ✅ Pass |
| Safari Mobile | `mobile_safari` | iOS PIN / Fingerprint | ✅ Pass |
| Brave Mobile | `mobile_brave` | iOS PIN / Fingerprint | ✅ Pass |
 
> 💡 The tunnel URL changes every time cloudflared restarts. Always copy the new URL and update RP_ID and ORIGIN.
 
---
 
## 🔌 API Endpoints
 
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the frontend single-page application |
| `POST` | `/register/begin` | Generate registration options with random challenge |
| `POST` | `/register/complete` | Verify attestation response and store credential |
| `POST` | `/authenticate/begin` | Generate authentication options with random challenge |
| `POST` | `/authenticate/complete` | Verify assertion response and create session |
| `GET` | `/protected` | Protected resource — requires authenticated session (HTTP 401 if not logged in) |
| `POST` | `/logout` | Clear authenticated session |
 
---
 
## 🔒 WebAuthn Flow
 
### Registration Flow
 
```
Browser                         Server (app.py)
   |                                |
   |--- POST /register/begin ------>|
   |    { username }                |-- Generate random 32-byte challenge
   |                                |-- Store challenge in session
   |<-- Registration Options -------|
   |    { challenge, rp, user,      |
   |      pubKeyCredParams }        |
   |                                |
   |-- navigator.credentials        |
   |      .create({ publicKey })    |
   |           |                    |
   |    Windows Hello / Authenticator
   |    generates key pair          |
   |    stores private key in TPM   |
   |           |                    |
   |<-- Attestation Response -------|
   |    { credential_id,            |
   |      public_key, signature }   |
   |                                |
   |--- POST /register/complete --->|
   |    { attestation response }    |-- Verify challenge ✓
   |                                |-- Verify origin ✓
   |                                |-- Verify RP ID hash ✓
   |                                |-- Verify UP flag ✓
   |                                |-- Verify attestation ✓
   |                                |-- Store public key + sign count
   |<-- { status: ok } -------------|
```
 
### Authentication Flow
 
```
Browser                         Server (app.py)
   |                                |
   |--- POST /authenticate/begin -->|
   |    { username }                |-- Generate random 32-byte challenge
   |                                |-- Store challenge in session
   |<-- Authentication Options -----|
   |    { challenge,                |
   |      allowCredentials }        |
   |                                |
   |-- navigator.credentials        |
   |      .get({ publicKey })       |
   |           |                    |
   |    Windows Hello / Authenticator
   |    signs challenge with        |
   |    private key from TPM        |
   |           |                    |
   |<-- Assertion Response ---------|
   |    { signature,                |
   |      authenticatorData }       |
   |                                |
   |--- POST /authenticate/complete>|
   |    { assertion response }      |-- Verify challenge ✓
   |                                |-- Verify origin ✓
   |                                |-- Verify RP ID hash ✓
   |                                |-- Verify UP flag ✓
   |                                |-- Verify signature with public key ✓
   |                                |-- Verify sign count > stored count ✓
   |                                |-- Update sign count
   |                                |-- Create authenticated session
   |<-- { status: ok, username } ---|
```
 
---
 
## ✅ Server Verification Steps
 
### Registration Verification (WebAuthn Spec §7.1)
 
| # | What is Verified | Spec Reference |
|---|---|---|
| 1 | `clientDataJSON.type` = `webauthn.create` 
| 2 | Challenge matches server-issued challenge
| 3 | Origin matches expected origin 
| 4 | RP ID hash in authenticatorData
| 5 | User-Present (UP) flag set 
| 6 | Attestation statement verified 
| 7 | Credential ID not already registered
 
### Authentication Verification (WebAuthn Spec §7.2)
 
| # | What is Verified | Spec Reference |
|---|---|---|
| 1 | `clientDataJSON.type` = `webauthn.get`
| 2 | Challenge matches server-issued challenge 
| 3 | Origin matches expected origin 
| 4 | RP ID hash in authenticatorData 
| 5 | User-Present (UP) flag set 
| 6 | Credential belongs to claimed user 
| 7 | Signature verified with stored public key 
| 8 | Sign count greater than stored count 
| 9 | Sign count updated after success 
 
---
 
## 🔬 Negative Tests
 
### Test 1 — Unregistered User
 
```
Steps:
1. Click Sign In tab
2. Enter username: hacker (never registered)
3. Click Sign In with Passkey
 
Server response (HTTP 400):
{"error": "No credentials registered for this user"}
```
 
### Test 2 — Tampered Signature
 
Open **F12 → Console** tab, paste this BEFORE clicking Sign In:
 
```javascript
const orig = navigator.credentials.get.bind(navigator.credentials);
navigator.credentials.get = async function(opts) {
  const r = await orig(opts);
  const sig = new Uint8Array(r.response.signature);
  sig[0] ^= 0xFF;
  return r;
};
console.log("Tamper active! Now click Sign In.");
```
 
```
Server response (HTTP 400):
{"error": "Authentication failed: Signature verification failed"}
```
 
### Test 3 — Foreign Credential
 
```
Steps:
1. Register user alice and user bob separately
2. Sign in as alice — copy rawId from F12 → Network → authenticate/complete → Payload tab
3. Open Console and run:
 
fetch('/authenticate/begin', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({username: 'bob'})
})
.then(r => r.json())
.then(() => fetch('/authenticate/complete', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    id: "PASTE_ALICE_RAWID_HERE",
    rawId: "PASTE_ALICE_RAWID_HERE",
    type: "public-key",
    response: { clientDataJSON: "x", authenticatorData: "x", signature: "x" }
  })
}))
.then(r => r.json())
.then(d => console.log(d));
 
Server response (HTTP 403):
{"error": "Credential does not belong to this user – access denied"}
```
4. If you are familiar with burp suite, you can use burp suite to intercept and modify package data
---
 
## ⚙️ Environment Variables
 
| Variable | Default | Description |
|---|---|---|
| `RP_ID` | `localhost` | Relying Party ID — must match the domain in browser URL |
| `ORIGIN` | `https://localhost:5000` | Full expected origin URL |
| `TLS_CERT` | `..\certs\cert.pem` | Path to TLS certificate |
| `TLS_KEY` | `..\certs\key.pem` | Path to TLS private key |
| `PORT` | `5000` | Server port number |
 
---
 
## 🛠️ Troubleshooting
 
| Error | Cause | Fix |
|---|---|---|
| `'python' is not recognized` | Python not added to PATH | Reinstall Python — check "Add to PATH" during install |
| `ModuleNotFoundError: webauthn.helpers` | Wrong webauthn package installed | `pip uninstall webauthn && pip install webauthn==2.7.1` |
| `The operation is insecure` | Using HTTP or IP address for WebAuthn | Use `https://localhost:5000` — not the IP |
| `Certificate warning in browser` | Self-signed certificate | Chrome/Edge: Advanced → Proceed / Firefox: Advanced → Accept Risk |
| `TLS certificate not found` | cert.pem or key.pem missing | Run OpenSSL command in Git Bash to generate certs |
| `ERR_EMPTY_RESPONSE` via tunnel | Server running HTTPS but tunnel expects HTTP | Set `TLS_CERT=notexist` to force HTTP mode |
| `RP ID not registrable domain suffix` | ngrok `.dev` domain blocked by WebAuthn | Use Cloudflare Tunnel — gives `.trycloudflare.com` domain |
| `Session expired` | Challenge lost between requests | Restart server and clear browser cookies |
| `AttributeError: attestation_type` | Wrong webauthn library version | Install exact version: `pip install webauthn==2.7.1` |
| `venv\Scripts\activate` fails | PowerShell execution policy | Run as admin: `Set-ExecutionPolicy RemoteSigned` |
| Port 5000 in use | Another app on port 5000 | `set PORT=8443` then use `https://localhost:8443` |
| Passkey already saved error | Credential already registered for this username | Use a new username or delete from `chrome://settings/passkeys` |
 
---
 
## 🔁 Quick Start Commands
 
### Desktop Testing (every time)
 
```cmd
cd "C:\Users\YourName\Desktop\webauthn-project\webauthn-project\server"
call ..\venv\Scripts\activate
set TLS_CERT=..\certs\cert.pem
set TLS_KEY=..\certs\key.pem
set RP_ID=localhost
set ORIGIN=https://localhost:5000
python app.py
```
 
Open: `https://localhost:5000`
 
---
 
### Mobile Testing (every time)
 
**Terminal 1 — Server:**
```cmd
cd "C:\Users\YourName\Desktop\webauthn-project\webauthn-project\server"
call ..\venv\Scripts\activate
set TLS_CERT=notexist
set TLS_KEY=notexist
set RP_ID=YOUR_TUNNEL.trycloudflare.com
set ORIGIN=https://YOUR_TUNNEL.trycloudflare.com
python app.py
```
 
**Terminal 2 — Tunnel:**
```cmd
C:\cloudflared\cloudflared.exe tunnel --url http://localhost:5000
```
 
Open on phone: `https://YOUR_TUNNEL.trycloudflare.com`
 
---
 
## 📚 References
 
- [WebAuthn Guide by Duo Security](https://webauthn.guide/)
- [SimpleWebAuthn Documentation](https://simplewebauthn.dev/docs/)
- [MDN Web Docs — Web Authentication API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Authentication_API)
- [W3C WebAuthn Level 2 Specification](https://www.w3.org/TR/webauthn-2/)
- [py_webauthn Library — Duo Labs](https://github.com/duo-labs/py_webauthn)
- [Cloudflare Tunnel Documentation](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/)
- [FIDO Alliance WebAuthn Overview](https://fidoalliance.org/fido2/fido2-web-authentication-webauthn/)
---
 
## 👥 Group Members
 
| Name | Student ID |
|---|---|
| Md Foysal Hossain | 1000060115 |
| Tanvir Ahmed Khan | 100006045 |
 
**Course:** CSE722 — Aplied Cryptography  
**Institution:** BRAC University  
**Submission Date:** May 8, 2026
