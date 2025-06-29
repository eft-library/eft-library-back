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

## Websocket

Websocket을 사용할건데, 별도의 서버로 구성하지 않고 FastAPI의 지원 기능을 사용해서 할 예정

일단은 대댓글 알림, 게시글 댓글 알림 정도만 할 거라서 그렇게 큰 문제는 없을 듯

추후 팔로우 기능을 만들어서 글이 작성되면 알림 주는 것도 괜찮을 듯