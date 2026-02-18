-- psql -d financial_assistant -f db.sql
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================
-- 뉴스 피드
-- ============================================
CREATE TABLE news (
  id BIGSERIAL PRIMARY KEY,
  title TEXT NOT NULL,
  content TEXT,
  category VARCHAR,
  upload_date VARCHAR,
  source VARCHAR,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 뉴스 일일 정리
-- ============================================
CREATE TABLE news_organize (
  id BIGSERIAL PRIMARY KEY,
  summary_date VARCHAR NOT NULL,
  category VARCHAR,
  content TEXT NOT NULL,
  source_news_ids BIGINT[],
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE news_organize IS '뉴스 일일 정리 (주제별 통합 브리핑)';
COMMENT ON COLUMN news_organize.id IS '정리 고유 식별자';
COMMENT ON COLUMN news_organize.summary_date IS '정리 대상 날짜 (YYYY.MM.DD)';
COMMENT ON COLUMN news_organize.category IS '카테고리 (Economy, Tech 등)';
COMMENT ON COLUMN news_organize.content IS '일일 정리 내용';
COMMENT ON COLUMN news_organize.source_news_ids IS '정리에 포함된 news ID 배열';
COMMENT ON COLUMN news_organize.created_at IS '레코드 생성 시간';
COMMENT ON COLUMN news_organize.updated_at IS '레코드 수정 시간';

COMMENT ON TABLE news IS '뉴스레터 원문 데이터';
COMMENT ON COLUMN news.id IS '뉴스 고유 식별자';
COMMENT ON COLUMN news.title IS '뉴스 제목';
COMMENT ON COLUMN news.content IS '뉴스 본문';
COMMENT ON COLUMN news.category IS '카테고리 (Economy, Tech 등)';
COMMENT ON COLUMN news.upload_date IS '뉴스 발행일';
COMMENT ON COLUMN news.source IS '뉴스 출처 (머니레터, Daily Byte 등)';
COMMENT ON COLUMN news.created_at IS '레코드 생성 시간';
COMMENT ON COLUMN news.updated_at IS '레코드 수정 시간';

-- ============================================
-- 유튜브 요약
-- ============================================
CREATE TABLE video (
  id BIGSERIAL PRIMARY KEY,
  title TEXT NOT NULL,
  channel_name VARCHAR,
  thumbnail_url TEXT,
  video_url TEXT,
  upload_date VARCHAR,
  subtitle TEXT,
  summary TEXT,
  highlights TEXT[],
  source VARCHAR,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE video IS '유튜브 영상 및 요약 데이터';
COMMENT ON COLUMN video.id IS '영상 고유 식별자';
COMMENT ON COLUMN video.title IS '영상 제목';
COMMENT ON COLUMN video.channel_name IS '유튜브 채널명';
COMMENT ON COLUMN video.thumbnail_url IS '썸네일 이미지 URL';
COMMENT ON COLUMN video.video_url IS '영상 URL';
COMMENT ON COLUMN video.upload_date IS '영상 업로드일';
COMMENT ON COLUMN video.subtitle IS '영상 자막';
COMMENT ON COLUMN video.summary IS '영상 내용 요약';
COMMENT ON COLUMN video.highlights IS '주요 키워드 배열';
COMMENT ON COLUMN video.source IS '영상 출처';
COMMENT ON COLUMN video.created_at IS '레코드 생성 시간';
COMMENT ON COLUMN video.updated_at IS '레코드 수정 시간';

-- ============================================
-- PDF 문서 메타데이터
-- ============================================
CREATE TABLE pdf_documents (
  id BIGSERIAL PRIMARY KEY,
  title VARCHAR NOT NULL,
  author VARCHAR,
  file_hash VARCHAR,
  total_pages INTEGER,
  category VARCHAR,
  description TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE pdf_documents IS 'PDF 문서 메타데이터';
COMMENT ON COLUMN pdf_documents.id IS 'PDF 문서 고유 식별자';
COMMENT ON COLUMN pdf_documents.title IS 'PDF 문서 제목';
COMMENT ON COLUMN pdf_documents.author IS '저자';
COMMENT ON COLUMN pdf_documents.file_hash IS '파일 해시값 (중복 체크용, SHA256)';
COMMENT ON COLUMN pdf_documents.total_pages IS '총 페이지 수';
COMMENT ON COLUMN pdf_documents.category IS '카테고리 (투자, 경제, 기술 등)';
COMMENT ON COLUMN pdf_documents.description IS '문서 설명';
COMMENT ON COLUMN pdf_documents.created_at IS '레코드 생성 시간';
COMMENT ON COLUMN pdf_documents.updated_at IS '레코드 수정 시간';

-- ============================================
-- 통합 임베딩 테이블
-- metadata 예시:
--   news: {"category": "Economy", "source": "머니레터"}
--   video: {"channel_name": "삼프로TV", "sentiment": "Positive"}
--   pdf: {"page_number": 5, "chunk_index": 3, "token_count": 450}
-- ============================================
CREATE TABLE embeddings (
  id BIGSERIAL PRIMARY KEY,
  source_type VARCHAR NOT NULL,
  source_id BIGINT NOT NULL,
  content TEXT NOT NULL,
  embedding vector(1024),
  metadata JSONB,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  UNIQUE(source_type, source_id)
);

COMMENT ON TABLE embeddings IS '통합 임베딩 테이블 (벡터 검색용)';
COMMENT ON COLUMN embeddings.id IS '임베딩 고유 식별자';
COMMENT ON COLUMN embeddings.source_type IS '원본 데이터 타입 (news, video, pdf)';
COMMENT ON COLUMN embeddings.source_id IS '원본 테이블의 ID';
COMMENT ON COLUMN embeddings.content IS '임베딩된 텍스트 원문';
COMMENT ON COLUMN embeddings.embedding IS '벡터 임베딩 (1024차원)';
COMMENT ON COLUMN embeddings.metadata IS '소스별 추가 메타데이터 (JSONB)';
COMMENT ON COLUMN embeddings.created_at IS '레코드 생성 시간';
COMMENT ON COLUMN embeddings.updated_at IS '레코드 수정 시간';

-- ============================================
-- 인덱스
-- 연산자
--  ┌────────┬────────────────────┐
--  │ 연산자   │        설명         │
--  ├────────┼────────────────────┤
--  │ <->    │ L2 거리 (유클리드)    │
--  ├────────┼────────────────────┤
--  │ <=>    │ 코사인 거리           │
--  ├────────┼────────────────────┤
--  │ <#>    │ 내적 (음수)          │
--  └────────┴────────────────────┘
-- ============================================
-- 벡터 검색 인덱스 (코사인 유사도)
CREATE INDEX embeddings_vector_idx
ON embeddings USING hnsw (embedding vector_cosine_ops);

-- 소스별 조회 인덱스
CREATE INDEX embeddings_source_idx ON embeddings(source_type, source_id);

-- ============================================
-- PDF 청크 테이블
-- ============================================
CREATE TABLE pdf_chunks (
  id BIGSERIAL PRIMARY KEY,
  document_id BIGINT NOT NULL REFERENCES pdf_documents(id),
  chunk_index INTEGER NOT NULL,
  content TEXT NOT NULL,
  page_start INTEGER,
  page_end INTEGER,
  token_count INTEGER,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE pdf_chunks IS 'PDF 문서 청크 데이터';
COMMENT ON COLUMN pdf_chunks.id IS '청크 고유 식별자';
COMMENT ON COLUMN pdf_chunks.document_id IS 'PDF 문서 ID (pdf_documents.id FK)';
COMMENT ON COLUMN pdf_chunks.chunk_index IS '청크 순서 인덱스';
COMMENT ON COLUMN pdf_chunks.content IS '청크 텍스트 내용';
COMMENT ON COLUMN pdf_chunks.page_start IS '시작 페이지';
COMMENT ON COLUMN pdf_chunks.page_end IS '종료 페이지';
COMMENT ON COLUMN pdf_chunks.token_count IS '토큰 수';
COMMENT ON COLUMN pdf_chunks.created_at IS '레코드 생성 시간';

-- ============================================
-- 일일 섹터 추천 리포트 테이블
-- ============================================
CREATE TABLE daily_reports (
  id BIGSERIAL PRIMARY KEY,
  report_date VARCHAR NOT NULL UNIQUE,
  content TEXT NOT NULL,
  sectors JSONB,
  source_count INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE daily_reports IS '일일 섹터 추천 리포트';
COMMENT ON COLUMN daily_reports.id IS '리포트 고유 식별자';
COMMENT ON COLUMN daily_reports.report_date IS '리포트 날짜 (YYYY.MM.DD)';
COMMENT ON COLUMN daily_reports.content IS '리포트 본문';
COMMENT ON COLUMN daily_reports.sectors IS '섹터별 추천 데이터 (JSONB)';
COMMENT ON COLUMN daily_reports.source_count IS '분석 소스 수';
COMMENT ON COLUMN daily_reports.created_at IS '레코드 생성 시간';
COMMENT ON COLUMN daily_reports.updated_at IS '레코드 수정 시간';

-- ============================================
-- 뉴스 소스 관리 테이블
-- ============================================
CREATE TABLE news_sources (
  id BIGSERIAL PRIMARY KEY,
  type VARCHAR NOT NULL,          -- 'email' | 'rss'
  identifier VARCHAR NOT NULL,    -- 이메일 주소 또는 RSS URL
  source_name VARCHAR NOT NULL,   -- '머니레터', 'Ars Technica' 등
  category VARCHAR NOT NULL,      -- 'Economy', 'Tech' 등
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(type, identifier)
);

COMMENT ON TABLE news_sources IS '뉴스 소스 관리 (이메일 발신자, RSS 피드)';
COMMENT ON COLUMN news_sources.id IS '소스 고유 식별자';
COMMENT ON COLUMN news_sources.type IS '소스 타입 (email, rss)';
COMMENT ON COLUMN news_sources.identifier IS '이메일 주소 또는 RSS URL';
COMMENT ON COLUMN news_sources.source_name IS '소스 이름 (머니레터, Ars Technica 등)';
COMMENT ON COLUMN news_sources.category IS '카테고리 (Economy, Tech 등)';
COMMENT ON COLUMN news_sources.is_active IS '활성화 여부';
COMMENT ON COLUMN news_sources.created_at IS '레코드 생성 시간';
COMMENT ON COLUMN news_sources.updated_at IS '레코드 수정 시간';

-- 초기 데이터: 이메일 뉴스레터
INSERT INTO news_sources (type, identifier, source_name, category) VALUES
  ('email', 'moneyletter@uppity.co.kr', '머니레터', 'Economy'),
  ('email', 'byteteam365@mydailybyte.com', 'Daily Byte', 'Tech'),
  ('email', 'miraklelab@mk.co.kr', '미라클레터', 'Economy'),
  ('email', 'morning@ilbuntok.com', '일분톡', 'Economy'),
  ('email', 'thecapitaledge+weeklyedge@substack.com', 'The Capital Edge', 'Economy');

-- 초기 데이터: RSS 피드
INSERT INTO news_sources (type, identifier, source_name, category) VALUES
  ('rss', 'https://arstechnica.com/ai/feed', 'Ars Technica', 'Tech'),
  ('rss', 'https://arstechnica.com/information-technology/feed', 'Ars Technica', 'Tech'),
  ('rss', 'https://techcrunch.com/feed', 'TechCrunch', 'Tech');

-- ============================================
-- 환율 이력 (USD/KRW)
-- ============================================
CREATE TABLE exchange_rate_history (
  id BIGSERIAL PRIMARY KEY,
  record_date VARCHAR NOT NULL,
  rate DECIMAL(12,4) NOT NULL,
  previous_rate DECIMAL(12,4),
  change_amount DECIMAL(12,4),
  change_percentage DECIMAL(8,4),
  source VARCHAR DEFAULT 'Yahoo Finance',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(record_date)
);

COMMENT ON TABLE exchange_rate_history IS 'USD/KRW 환율 이력';
COMMENT ON COLUMN exchange_rate_history.id IS '환율 이력 고유 식별자';
COMMENT ON COLUMN exchange_rate_history.record_date IS '기록 날짜 (YYYY-MM-DD)';
COMMENT ON COLUMN exchange_rate_history.rate IS '종가 환율';
COMMENT ON COLUMN exchange_rate_history.previous_rate IS '전일 종가 환율';
COMMENT ON COLUMN exchange_rate_history.change_amount IS '변동 금액';
COMMENT ON COLUMN exchange_rate_history.change_percentage IS '변동률 (%)';
COMMENT ON COLUMN exchange_rate_history.source IS '데이터 출처';
COMMENT ON COLUMN exchange_rate_history.created_at IS '레코드 생성 시간';
COMMENT ON COLUMN exchange_rate_history.updated_at IS '레코드 수정 시간';

-- ============================================
-- 공포/탐욕 지수
-- ============================================
CREATE TABLE fear_greed_index (
  id BIGSERIAL PRIMARY KEY,
  record_date VARCHAR NOT NULL,
  value INTEGER NOT NULL,
  label VARCHAR NOT NULL,
  source VARCHAR DEFAULT 'CNN',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(record_date)
);

COMMENT ON TABLE fear_greed_index IS 'CNN 공포/탐욕 지수 이력';
COMMENT ON COLUMN fear_greed_index.id IS '지수 이력 고유 식별자';
COMMENT ON COLUMN fear_greed_index.record_date IS '기록 날짜 (YYYY-MM-DD)';
COMMENT ON COLUMN fear_greed_index.value IS '공포/탐욕 지수 (0~100)';
COMMENT ON COLUMN fear_greed_index.label IS '지수 라벨 (Extreme Fear/Fear/Neutral/Greed/Extreme Greed)';
COMMENT ON COLUMN fear_greed_index.source IS '데이터 출처';
COMMENT ON COLUMN fear_greed_index.created_at IS '레코드 생성 시간';
COMMENT ON COLUMN fear_greed_index.updated_at IS '레코드 수정 시간';

-- ============================================
-- 유튜브 채널 소스 관리 테이블
-- ============================================
CREATE TABLE video_sources (
  id BIGSERIAL PRIMARY KEY,
  channel_handle VARCHAR NOT NULL UNIQUE,  -- '@TTimesTV' 등 채널 핸들
  channel_name VARCHAR NOT NULL,           -- 'TTimesTV' 등 표시 이름
  category VARCHAR NOT NULL,               -- 'Economy', 'Tech' 등
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE video_sources IS '유튜브 채널 소스 관리';
COMMENT ON COLUMN video_sources.id IS '소스 고유 식별자';
COMMENT ON COLUMN video_sources.channel_handle IS '유튜브 채널 핸들 (@channel)';
COMMENT ON COLUMN video_sources.channel_name IS '채널 표시 이름';
COMMENT ON COLUMN video_sources.category IS '카테고리 (Economy, Tech 등)';
COMMENT ON COLUMN video_sources.is_active IS '활성화 여부';
COMMENT ON COLUMN video_sources.created_at IS '레코드 생성 시간';
COMMENT ON COLUMN video_sources.updated_at IS '레코드 수정 시간';

-- 초기 데이터: 유튜브 채널
INSERT INTO video_sources (channel_handle, channel_name, category) VALUES
  ('@TTimesTV', 'TTimesTV', 'Economy'),
  ('@unrealtech', 'unrealtech', 'Tech'),
  ('@softdragon', 'softdragon', 'Tech');
