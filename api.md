# 1. 뉴스 피드
## 뉴스 피드 조회
### GET /api/news
```json
[
  {
    "id": "string",
    "title": "뉴스 제목",
    "summary": "목록에서 보여줄 짧은 요약",
    "content": "뉴스 본문 전체 (프론트엔드 Gemini 분석용)",
    "category": "Tech | Economy | Science | Global",
    "imageUrl": "이미지 URL",
    "date": "YYYY.MM.DD",
    "source": "언론사"
  }
]
```

# 2. Youtube summary
## 유튜브 요약본 조회
### GET /api/youtube/videos
백엔드 필수 로직:
- 유튜브 영상 목록 및 자막 추출
- LLM을 통한 요약문 생성 (마크다운 불렛포인트 권장)
- 핵심 키워드 및 시장 감성(Sentiment) 분석
```json
[
  {
    "id": "영상 고유 ID",
    "title": "영상 제목",
    "channelName": "채널 이름",
    "thumbnailUrl": "썸네일 URL",
    "videoUrl": "유튜브 원본 주소",
    "date": "YYYY.MM.DD",
    "summary": "AI가 요약한 핵심 내용 (줄바꿈 포함)",
    "highlights": ["키워드1", "키워드2"],
    "sentiment": "Positive | Neutral | Negative"
  }
]
```

# 3. 투자 지표, 상담 API
## 환율
### GET /api/investment/exchange-rate
```json
{
  "rate": 1342.50, 
  "change": 0.25, 
  "lastUpdated": "HH:mm:ss"
}
```

## 시장 지수
### GET /api/investment/market-index
```json
[{"date": "MM-DD", "close": 6915.61}, ...]
```

## 공포 지수
### GET /api/investment/fear-greed-index
```json
{
  "value": 68, 
  "label": "Greed"
}
```
