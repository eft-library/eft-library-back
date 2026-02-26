-- pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- RAG 문서 테이블
CREATE TABLE IF NOT EXISTS rag_documents (
    id            BIGSERIAL PRIMARY KEY,
    source_table  TEXT NOT NULL,              -- 'story_i18n'
    source_id     TEXT NOT NULL,              -- story_i18n.id
    lang          TEXT NOT NULL,              -- 'ko' | 'en' | 'ja'
    content       TEXT NOT NULL,              -- 임베딩용 조합 텍스트
    embedding     VECTOR(1024),               -- bge-m3 차원
    metadata      JSONB DEFAULT '{}',         -- 검색 후 참조할 원본 데이터
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    updated_at    TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (source_table, source_id, lang)    -- 중복 방지
);

-- 벡터 검색 인덱스
CREATE INDEX IF NOT EXISTS rag_documents_embedding_idx
    ON rag_documents
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- 검색 필터용 인덱스
CREATE INDEX IF NOT EXISTS rag_documents_source_idx
    ON rag_documents (source_table, lang);

-- 채팅 세션 테이블
CREATE TABLE IF NOT EXISTS chat_sessions (
    id            BIGSERIAL PRIMARY KEY,
    session_id    UUID DEFAULT gen_random_uuid() UNIQUE,
    user_id       TEXT,
    lang          TEXT DEFAULT 'ko',          -- 세션 기본 언어
    metadata      JSONB DEFAULT '{}',
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    updated_at    TIMESTAMPTZ DEFAULT NOW()
);

-- 채팅 메시지 테이블
CREATE TABLE IF NOT EXISTS chat_messages (
    id            BIGSERIAL PRIMARY KEY,
    session_id    UUID NOT NULL REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
    role          TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content       TEXT NOT NULL,
    source_docs   JSONB DEFAULT '[]',         -- 참조한 RAG 문서 목록
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- 메시지 조회용 인덱스
CREATE INDEX IF NOT EXISTS chat_messages_session_idx
    ON chat_messages (session_id, created_at);

-- updated_at 자동 갱신 함수
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER rag_documents_updated_at
    BEFORE UPDATE ON rag_documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER chat_sessions_updated_at
    BEFORE UPDATE ON chat_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();