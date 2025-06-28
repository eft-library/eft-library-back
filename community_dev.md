# 백엔드 (FastAPI) 측 기술

## FastAPI WebSocket or Socket.IO 연동

실시간 기능이 필요하면 WebSocket을 FastAPI에서 구현

```
[사용자 작성 → React Query mutation 요청] 
     → [FastAPI API 처리 + DB 저장] 
         → [WebSocket or polling 통해 다른 사용자에게 실시간 갱신 전파]
             → [프론트에서 useQuery or SWR로 자동 반영]
```

## Kafka 활용

댓글 알림, 통계에 활용하면 될 듯

```
[1] 사용자 → FastAPI (댓글 작성 API 호출)
      ↓
[2] FastAPI → Kafka (댓글 작성 이벤트 발행)
      ↓
[3] Kafka Consumer → (필요한 후처리: 알림 저장, 브로드캐스트, WebSocket 푸시 등)
      ↓
[4] Next.js → WebSocket으로 실시간 UI 갱신

```