from external.gmail_client import fetch_emails


def get_emails_from_sender(sender_email: str, max_results: int = 10) -> list[dict]:
    """특정 발신자로부터 이메일을 가져옵니다."""
    return fetch_emails(sender_email, max_results)
