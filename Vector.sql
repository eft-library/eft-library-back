-- 재설계 필요

-- pgvector extension (아직 없으면)
CREATE EXTENSION IF NOT EXISTS vector;

-- RAG 문서 테이블
CREATE TABLE IF NOT EXISTS rag_documents (
    id            BIGSERIAL PRIMARY KEY,
    source_table  TEXT NOT NULL,
    source_id     TEXT NOT NULL,
    lang          TEXT NOT NULL,
    content       TEXT NOT NULL,
    embedding     VECTOR(1024),
    chunk_type    TEXT NOT NULL DEFAULT 'content',  -- 추가
    ref_type      TEXT,                             -- 추가
    ref_id        TEXT,                             -- 추가
    metadata      JSONB DEFAULT '{}',
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    updated_at    TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (source_table, source_id, lang, chunk_type)  -- chunk_type 추가
);

-- 벡터 검색 인덱스
CREATE INDEX IF NOT EXISTS rag_documents_embedding_idx ON rag_documents USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
-- 검색 필터용 인덱스
CREATE INDEX IF NOT EXISTS rag_documents_source_idx
    ON rag_documents (source_table, lang);
-- 추가
CREATE INDEX IF NOT EXISTS rag_documents_chunk_type_idx
    ON rag_documents (chunk_type, ref_type);
-- trgm 인덱스 추가
CREATE INDEX idx_rag_documents_content_trgm
ON rag_documents
USING GIN (content gin_trgm_ops)
WHERE chunk_type = 'identifier';

-- 채팅 세션 테이블
CREATE TABLE IF NOT EXISTS chat_sessions (
    id            BIGSERIAL PRIMARY KEY,
    session_id    UUID DEFAULT gen_random_uuid() UNIQUE,
    user_id       TEXT,
    lang          TEXT DEFAULT 'ko',
    metadata      JSONB DEFAULT '{}',
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    updated_at    TIMESTAMPTZ DEFAULT NOW()
);

-- 채팅 메시지 테이블
CREATE TABLE IF NOT EXISTS chat_messages (
    id            BIGSERIAL PRIMARY KEY,
    session_id    UUID,
    role          TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content       TEXT NOT NULL,
    lang          TEXT,
    source_docs   JSONB DEFAULT '[]',
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- 세션별 메시지 조회 (멀티턴 히스토리)
CREATE INDEX IF NOT EXISTS chat_messages_session_idx
    ON chat_messages (session_id, created_at);

-- 히스토리 분석용 (세션 없어도 조회 가능)
CREATE INDEX IF NOT EXISTS chat_messages_lang_idx
    ON chat_messages (lang, created_at);

CREATE INDEX IF NOT EXISTS chat_messages_role_idx
    ON chat_messages (role, created_at);

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