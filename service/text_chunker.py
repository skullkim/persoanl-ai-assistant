def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """텍스트를 고정 크기 청크로 분할합니다.

    Args:
        text: 분할할 텍스트
        chunk_size: 청크 크기 (문자 수)
        overlap: 오버랩 크기 (문자 수)

    Returns:
        청크 리스트
    """
    if not text or not text.strip():
        return []

    text = text.strip()

    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        if end < len(text):
            # 문장 경계에서 끊기 시도
            boundary = text.rfind(". ", start, end)
            if boundary == -1:
                boundary = text.rfind("\n", start, end)
            if boundary > start:
                end = boundary + 1

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - overlap
        if start >= len(text):
            break

    return chunks


def chunk_pages(pages: list[tuple[int, str]], chunk_size: int = 1000, overlap: int = 200) -> list[dict]:
    """페이지별 텍스트를 청크로 분할하고 페이지 정보를 유지합니다.

    Args:
        pages: [(page_number, text), ...] 리스트
        chunk_size: 청크 크기
        overlap: 오버랩 크기

    Returns:
        [{"content": str, "page_start": int, "page_end": int, "chunk_index": int}, ...]
    """
    # 전체 텍스트와 페이지 경계 추적
    full_text = ""
    page_boundaries = []  # [(start_offset, page_number), ...]

    for page_num, text in pages:
        page_boundaries.append((len(full_text), page_num))
        full_text += text + "\n"

    if not full_text.strip():
        return []

    chunks = chunk_text(full_text, chunk_size, overlap)

    result = []
    text_offset = 0

    for idx, chunk in enumerate(chunks):
        chunk_start = full_text.find(chunk, text_offset)
        if chunk_start == -1:
            chunk_start = text_offset
        chunk_end = chunk_start + len(chunk)

        page_start = page_boundaries[0][1]
        page_end = page_boundaries[-1][1]

        for i, (offset, page_num) in enumerate(page_boundaries):
            if offset <= chunk_start:
                page_start = page_num
            if offset <= chunk_end:
                page_end = page_num

        result.append({
            "content": chunk,
            "page_start": page_start,
            "page_end": page_end,
            "chunk_index": idx,
        })

        text_offset = chunk_start + 1

    return result
