🚀 Mac mini M4 Pro 기반 AI 백엔드 개발 지침서
1. 프로젝트 개요
- 목표: 유튜브 자막, 뉴스레터(Email), PDF 도서를 수집하여 투자 분야를 분석하는 AI 백엔드 구축.
- 하드웨어 환경: 
  - WAS: Mac mini M4 Pro (14코어 CPU, 20코어 GPU, 48GB 통합 메모리, 1TB SSD).
  - DB: Mac mini 2012 (intel i5 2세대, 4코어 8 스레드 CPU, 16GB DDR3 RAM, 512GB SSD).
- 핵심 제약: 
  - Backend, LLM 엔진 는 단일 M4 Pro Mac mini 내부에서 로컬로 구동됨.
  - DB는 단일 Mac mini 2012 내부에서 구동됨.

2. 기술 스택 및 연동 방식
- 언어: Python 3.10+
- 프레임워크: FastAPI (비동기 처리 필수)
- LLM 엔진: Ollama (로컬 서버 localhost:11434 활용)
- LLM 프레임워크: LangChain (Langchain-Ollama 패키지 사용)
- 데이터베이스: PostgreSQL (Vector DB 확장을 위한 pgvector)

3. 모델 운용 전략 (중요)
- 48GB 메모리를 효율적으로 사용하기 위해 다음 모델들을 상황에 맞게 오케스트레이션해야 함:
- 임베딩: mxbai-embed-large 또는 bge-m3 (상시 로드)
- 요약/전처리: llama3.1:8b 또는 gemma2:9b (빠른 처리용)
- 심층 분석: llama3.1:70b (고지능 추론용, 필요 시 로드)
- 지침: Ollama의 keep_alive 설정을 활용하여 모델 전환 시 메모리 충돌이 없도록 코드를 설계할 것.

4. 코드 아키텍처 가이드라인 (Layered Architecture)
   코드는 다음 구조를 유지하며 확장 가능해야 함:
- api/: 엔드포인트 정의 및 요청 유효성 검사.
- services/: 비즈니스 로직 및 LangChain을 활용한 AI 워크플로우 (요약 -> 분석).
- external/: DB, 유튜브 자막(youtube-transcript-api), 이메일, PDF 파싱, 등 외부 리소스 조회 / 수정 모듈
- config/: 설정 파일
- batch/: 데이터 ETL 관련 배치

5. 데이터베이스
- 데이터베이스 DDL은 db.sql에 존재

6. CLAUDE 에게 주는 특명
- "비동기(Async) 우선": LLM 추론은 시간이 걸리므로 반드시 비동기 함수로 작성하여 서버가 블로킹되지 않게 하라.
- "로컬 경로 최적화": 모든 데이터 저장은 Mac mini 내부 ./data 경로를 기준으로 관리하라.
- "에러 핸들링": Ollama 서버 연결 실패나 모델 로드 시간 초과에 대한 예외 처리를 반드시 포함하라.
