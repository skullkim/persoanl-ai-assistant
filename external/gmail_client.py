import json
import re
import base64
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from bs4 import BeautifulSoup

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

DATA_DIR = Path("./data")
TOKEN_PATH = DATA_DIR / "gmail_token.json"
CREDENTIALS_PATH = DATA_DIR / "gmail_credentials.json"


def _load_client_config() -> dict:
    """credentials 파일에서 client_id와 client_secret을 로드합니다."""
    with open(CREDENTIALS_PATH) as f:
        config = json.load(f)
    # "installed" 또는 "web" 키 확인
    return config.get("installed") or config.get("web") or {}


def _save_token(creds: Credentials, client_config: dict):
    """토큰을 client_id, client_secret 포함하여 저장합니다."""
    token_data = json.loads(creds.to_json())
    token_data["client_id"] = client_config.get("client_id")
    token_data["client_secret"] = client_config.get("client_secret")
    TOKEN_PATH.write_text(json.dumps(token_data, indent=2))


def get_gmail_service():
    """Gmail API 서비스 인스턴스를 반환합니다."""
    DATA_DIR.mkdir(exist_ok=True)

    if not CREDENTIALS_PATH.exists():
        raise FileNotFoundError(
            f"Gmail 인증 파일이 필요합니다: {CREDENTIALS_PATH}\n"
            "Google Cloud Console에서 OAuth 2.0 클라이언트 ID를 생성하고 "
            "JSON 파일을 다운로드하세요."
        )

    client_config = _load_client_config()
    creds = None

    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            _save_token(creds, client_config)
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_PATH), SCOPES
            )
            creds = flow.run_local_server(port=0)
            _save_token(creds, client_config)

    return build("gmail", "v1", credentials=creds)


def fetch_emails(sender_email: str, max_results: int = 10) -> list[dict]:
    """특정 발신자의 이메일 목록을 가져옵니다."""
    service = get_gmail_service()

    query = f"from:{sender_email}"
    results = service.users().messages().list(
        userId="me",
        q=query,
        maxResults=max_results
    ).execute()

    messages = results.get("messages", [])
    emails = []

    for msg in messages:
        msg_detail = service.users().messages().get(
            userId="me",
            id=msg["id"],
            format="full"
        ).execute()

        headers = msg_detail.get("payload", {}).get("headers", [])
        header_dict = {h["name"]: h["value"] for h in headers}

        body = _extract_body(msg_detail.get("payload", {}))

        emails.append({
            "id": msg["id"],
            "thread_id": msg.get("threadId"),
            "subject": header_dict.get("Subject", "(제목 없음)"),
            "sender": header_dict.get("From", ""),
            "date": header_dict.get("Date", ""),
            "snippet": msg_detail.get("snippet", ""),
            "body": body,
        })

    return emails


def _html_to_text(html: str) -> str:
    """HTML을 읽기 쉬운 텍스트로 변환합니다."""
    soup = BeautifulSoup(html, "html.parser")

    # 스크립트, 스타일 태그 제거
    for tag in soup(["script", "style", "head", "meta", "link"]):
        tag.decompose()

    # 줄바꿈 처리
    for br in soup.find_all("br"):
        br.replace_with("\n")
    for p in soup.find_all("p"):
        p.insert_after("\n\n")
    for div in soup.find_all("div"):
        div.insert_after("\n")

    # 텍스트 추출
    text = soup.get_text()

    # 연속된 공백/줄바꿈 정리
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = text.strip()

    return text


def _extract_body(payload: dict) -> str:
    """이메일 본문을 추출합니다."""
    plain_text = ""
    html_text = ""

    if "body" in payload and payload["body"].get("data"):
        content = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")
        # HTML인지 확인
        if "<html" in content.lower() or "<body" in content.lower():
            html_text = content
        else:
            plain_text = content
    elif "parts" in payload:
        for part in payload["parts"]:
            mime_type = part.get("mimeType", "")
            data = part.get("body", {}).get("data", "")

            if mime_type == "text/plain" and data:
                plain_text = base64.urlsafe_b64decode(data).decode("utf-8")
            elif mime_type == "text/html" and data:
                html_text = base64.urlsafe_b64decode(data).decode("utf-8")
            elif "parts" in part:
                # 중첩된 multipart 처리
                nested = _extract_body(part)
                if nested:
                    plain_text = nested

    # plain text 우선, 없으면 HTML 변환
    if plain_text:
        return plain_text.strip()
    elif html_text:
        return _html_to_text(html_text)

    return ""
