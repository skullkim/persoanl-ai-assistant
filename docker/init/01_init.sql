-- Financial Investment Assistant Database Schema
-- pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================
-- 뉴스 피드
-- ============================================
CREATE TABLE news (
  id BIGSERIAL PRIMARY KEY,
  title TEXT NOT NULL,
  summary TEXT,
  content TEXT,
  category VARCHAR,
  upload_date VARCHAR,
  source VARCHAR,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE news IS '뉴스레터 원문 데이터';
COMMENT ON COLUMN news.id IS '뉴스 고유 식별자';
COMMENT ON COLUMN news.title IS '뉴스 제목';
COMMENT ON COLUMN news.summary IS '뉴스 요약';
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
  summary TEXT,
  highlights TEXT[],
  source VARCHAR,
  sentiment VARCHAR,
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
COMMENT ON COLUMN video.summary IS '영상 내용 요약';
COMMENT ON COLUMN video.highlights IS '주요 키워드 배열';
COMMENT ON COLUMN video.source IS '영상 출처';
COMMENT ON COLUMN video.sentiment IS '감성 분석 결과 (Positive, Negative, Neutral)';
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
-- ============================================
-- 벡터 검색 인덱스 (코사인 유사도)
CREATE INDEX embeddings_vector_idx
ON embeddings USING hnsw (embedding vector_cosine_ops);

-- 소스별 조회 인덱스
CREATE INDEX embeddings_source_idx ON embeddings(source_type, source_id);
