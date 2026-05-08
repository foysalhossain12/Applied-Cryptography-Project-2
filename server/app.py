import os
import base64
import secrets
import ssl
from flask import Flask, request, jsonify, session, send_from_directory
from flask_session import Session
import webauthn
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    UserVerificationRequirement,
    ResidentKeyRequirement,
    PublicKeyCredentialDescriptor,
    AuthenticatorTransport,
)
from webauthn.helpers.cose import COSEAlgorithmIdentifier
from dataclasses import dataclass
from typing import Dict, List
import datetime

app = Flask(__name__, static_folder="../client", static_url_path="")
app.secret_key = secrets.token_hex(32)

session_dir = os.path.join(os.environ.get("TEMP", "C:\\Temp"), "flask_sessions")
os.makedirs(session_dir, exist_ok=True)
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = session_dir
app.config["SESSION_PERMANENT"] = False
Session(app)

RP_ID   = os.environ.get("RP_ID", "localhost")
RP_NAME = "CSE722 WebAuthn Demo"
ORIGIN  = os.environ.get("ORIGIN", "https://localhost:5000")

user_db: Dict[str, dict] = {}


@dataclass
class CredentialRecord:
    credential_id: bytes
    public_key: bytes
    sign_count: int
    transports: List[str]
    aaguid: str
    attestation_type: str
    registered_at: str = ""
    last_used: str = ""


def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _get_user(username):
    return user_db.get(username)


def _get_or_create_user(username):
    if username not in user_db:
        user_db[username] = {
            "id": secrets.token_bytes(16),
            "username": username,
            "credentials": [],
        }
    return user_db[username]


def _find_credential(user, cred_id_bytes):
    for c in user["credentials"]:
        if c.credential_id == cred_id_bytes:
            return c
    return None


def _all_descriptors(user):
    descriptors = []
    for c in user["credentials"]:
        transports = []
        for t in c.transports:
            try:
                transports.append(AuthenticatorTransport(t))
            except ValueError:
                pass
        descriptors.append(
            PublicKeyCredentialDescriptor(
                id=c.credential_id,
                transports=transports if transports else None,
            )
        )
    return descriptors


def _get_attr(obj, *names, default="none"):
    for name in names:
        if hasattr(obj, name):
            val = getattr(obj, name)
            if val is not None:
                return str(val)
    return default


@app.route("/")
def index():
    return send_from_directory("../client", "index.html")


@app.route("/register/begin", methods=["POST"])
def register_begin():
    data = request.get_json()
    username = data.get("username", "").strip()
    if not username:
        return jsonify({"error": "Username required"}), 400

    user = _get_or_create_user(username)
    challenge = secrets.token_bytes(32)
    session["reg_challenge"] = challenge
    session["reg_username"] = username

    exclude = []
    for c in user["credentials"]:
        exclude.append({
            "type": "public-key",
            "id": b64url_encode(c.credential_id)
        })

    return jsonify({
        "challenge": b64url_encode(challenge),
        "rp": {"id": RP_ID, "name": RP_NAME},
        "user": {
            "id": b64url_encode(user["id"]),
            "name": username,
            "displayName": username,
        },
        "pubKeyCredParams": [
            {"type": "public-key", "alg": -7},
            {"type": "public-key", "alg": -257},
        ],
        "timeout": 60000,
        "excludeCredentials": exclude,
        "authenticatorSelection": {
            "residentKey": "preferred",
            "userVerification": "preferred",
        },
        "attestation": "direct",
    })


@app.route("/register/complete", methods=["POST"])
def register_complete():
    username = session.get("reg_username")
    challenge = session.get("reg_challenge")
    if not username or not challenge:
        return jsonify({"error": "Session expired"}), 400

    body = request.get_json()
    try:
        verification = webauthn.verify_registration_response(
            credential=body,
            expected_challenge=challenge,
            expected_rp_id=RP_ID,
            expected_origin=ORIGIN,
            require_user_verification=False,
        )
    except Exception as e:
        return jsonify({"error": f"Registration failed: {str(e)}"}), 400

    # webauthn 2.7.1 compatible attribute reading
    aaguid = _get_attr(verification, 'aaguid', default="00000000-0000-0000-0000-000000000000")
    attest_type = _get_attr(verification, 'fmt', 'attestation_type', 'attestation_object', default="none")

    user = _get_user(username)
    cred = CredentialRecord(
        credential_id=verification.credential_id,
        public_key=verification.credential_public_key,
        sign_count=verification.sign_count,
        transports=body.get("response", {}).get("transports", []),
        aaguid=aaguid,
        attestation_type=attest_type,
        registered_at=datetime.datetime.utcnow().isoformat() + "Z",
    )
    user["credentials"].append(cred)
    session.pop("reg_challenge", None)
    session.pop("reg_username", None)

    return jsonify({
        "status": "ok",
        "credentialId": b64url_encode(verification.credential_id),
        "aaguid": aaguid,
        "attestationType": attest_type,
    })


@app.route("/authenticate/begin", methods=["POST"])
def authenticate_begin():
    data = request.get_json()
    username = data.get("username", "").strip()
    if not username:
        return jsonify({"error": "Username required"}), 400

    user = _get_user(username)
    if not user or not user["credentials"]:
        return jsonify({"error": "No credentials registered for this user"}), 400

    challenge = secrets.token_bytes(32)
    session["auth_challenge"] = challenge
    session["auth_username"] = username

    allow = []
    for c in user["credentials"]:
        allow.append({
            "type": "public-key",
            "id": b64url_encode(c.credential_id)
        })

    return jsonify({
        "challenge": b64url_encode(challenge),
        "allowCredentials": allow,
        "userVerification": "preferred",
        "timeout": 60000,
        "rpId": RP_ID,
    })


@app.route("/authenticate/complete", methods=["POST"])
def authenticate_complete():
    username = session.get("auth_username")
    challenge = session.get("auth_challenge")
    if not username or not challenge:
        return jsonify({"error": "Session expired"}), 400

    body = request.get_json()
    user = _get_user(username)
    if not user:
        return jsonify({"error": "User not found"}), 400

    try:
        raw_id = base64.urlsafe_b64decode(body["rawId"] + "==")
    except Exception:
        return jsonify({"error": "Invalid credential ID"}), 400

    cred = _find_credential(user, raw_id)
    if not cred:
        return jsonify({
            "error": "Credential does not belong to this user - access denied"
        }), 403

    try:
        verification = webauthn.verify_authentication_response(
            credential=body,
            expected_challenge=challenge,
            expected_rp_id=RP_ID,
            expected_origin=ORIGIN,
            credential_public_key=cred.public_key,
            credential_current_sign_count=cred.sign_count,
            require_user_verification=False,
        )
    except Exception as e:
        return jsonify({"error": f"Authentication failed: {str(e)}"}), 400

    if verification.new_sign_count <= cred.sign_count and cred.sign_count != 0:
        return jsonify({
            "error": "Sign count check failed - possible cloned authenticator"
        }), 400

    cred.sign_count = verification.new_sign_count
    cred.last_used = datetime.datetime.utcnow().isoformat() + "Z"

    session.pop("auth_challenge", None)
    session.pop("auth_username", None)

    authenticator_info = {
        "aaguid": cred.aaguid,
        "attestationType": cred.attestation_type,
        "transports": cred.transports,
        "signCount": cred.sign_count,
        "registeredAt": cred.registered_at,
        "lastUsed": cred.last_used,
    }

    session["logged_in"] = True
    session["logged_in_username"] = username
    session["authenticator_info"] = authenticator_info

    return jsonify({
        "status": "ok",
        "username": username,
        "authenticator": authenticator_info,
    })


@app.route("/protected")
def protected():
    if not session.get("logged_in"):
        return jsonify({"error": "Not authenticated"}), 401
    return jsonify({
        "username": session["logged_in_username"],
        "authenticator": session.get("authenticator_info", {}),
    })


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    cert = os.environ.get("TLS_CERT", "..\\certs\\cert.pem")
    key  = os.environ.get("TLS_KEY",  "..\\certs\\key.pem")
    port = int(os.environ.get("PORT", 5000))

    if os.path.exists(cert) and os.path.exists(key):
        print(f"[+] Starting HTTPS server on port {port}")
        print(f"[+] RP_ID={RP_ID}  ORIGIN={ORIGIN}")
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert, key)
        app.run(host="0.0.0.0", port=port, ssl_context=context, debug=False)
    else:
        print("[!] TLS certificate not found - falling back to HTTP")
        app.run(host="0.0.0.0", port=port, debug=True)