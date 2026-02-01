## 1. 뉴스 피드 (News API)
날짜 기반 무한 스크롤을 위해 `offsetDays`와 `countDays` 파라미터를 사용합니다.

### GET /api/news
**Query Parameters:**
- `offsetDays` (int, optional, default: 0): 기준일로부터의 과거 오프셋 (0 = 오늘, 1 = 어제...)
- `countDays` (int, optional, default: 3): 가져올 날짜의 범위 (예: 3이면 3일치 데이터)

**Response:**
```json
[
  {
    "id": "news-20240521-01",
    "title": "뉴스 제목",
    "summary": "리스트용 요약",
    "content": "분석용 전체 본문",
    "category": "Tech | Economy | Science | Global",
    "date": "2024.05.21",
    "source": "언론사"
  }
]
```

---

## 2. 유튜브 영상 요약 (YouTube Insights API)
영상 자막 분석 및 요약 기능이 포함된 엔드포인트입니다.

### GET /api/youtube/videos
**Query Parameters:**
- `offsetDays` (int, default: 0): 뉴스 API와 동일한 방식
- `countDays` (int, default: 3): 뉴스 API와 동일한 방식

**백엔드 필수 구현 로직:**
1. 지정된 날짜 범위의 영상 리스트 수집
2. **LLM 처리**: 영상 자막을 추출하여 불렛포인트 형식의 `summary` 생성
3. **Sentiment**: 투자 관점에서의 긍정/중립/부정 판별

**Response:**
```json
[
  {
    "id": "yt-20240521-01",
    "title": "영상 제목",
    "channelName": "채널명",
    "thumbnailUrl": "이미지 URL",
    "videoUrl": "유튜브 링크",
    "date": "2024.05.21",
    "summary": "AI가 요약한 핵심 내용 (줄바꿈 포함)",
    "highlights": ["키워드1", "키워드2"],
    "sentiment": "Positive | Neutral | Negative"
  }
]
```

---

## 3. 투자 지표 API (Investment Metrics)
실시간성 지표를 제공합니다.

### GET /api/investment/exchange-rate
**Response:**
```json
{
  "rate": 1342.50, 
  "change": 0.25, 
  "lastUpdated": "HH:mm:ss"
}
```

### GET /api/investment/market-index
7일간의 추세 데이터를 반환합니다.
**Response:**
```json
[
  {"date": "05-21", "close": 6915.61},
  {"date": "05-20", "close": 6850.12},
  ...
]
```

### GET /api/investment/fear-greed-index
**Response:**
```json
{
  "value": 68, 
  "label": "Greed"
}
```

---
