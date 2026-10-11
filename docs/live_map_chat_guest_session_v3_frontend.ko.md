# V3 비로그인 채팅: 서버 발급 익명 쿠키 연동

## 목적

비로그인 사용자의 채팅 연결 제한을 IP 대신 서버 발급 익명 세션으로 적용한다. Next.js 서버나 프록시를 거쳐도 각 브라우저의 쿠키로 구분한다. 로그인 사용자는 기존 계정 기준이다. DB 마이그레이션이나 신규 환경 변수는 없다. 기존 공유 Redis를 사용한다.

프론트에서 랜덤 ID를 만들지 않는다. 백엔드가 발급하는 쿠키를 브라우저가 저장하고 전송한다. localStorage 저장과 토큰을 URL에 붙이는 처리는 필요 없다.

## 1. 연결 전에 쿠키 발급

로그인하지 않은 상태에서 채팅을 연결하기 전에 다음 요청을 보낸다.

```http
POST /api/live-map/v3/chat/guest-session
Content-Type: application/json

{}
```

```ts
const response = await fetch(`${apiOrigin}/api/live-map/v3/chat/guest-session`, {
  method: 'POST',
  credentials: 'include',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({}),
  cache: 'no-store',
});
if (!response.ok) {
  // 오류 상태를 표시하고 지연 후 재시도한다. 아직 WebSocket을 열지 않는다.
  throw new Error('게스트 채팅 세션 발급 실패');
}
```

성공 응답은 `200`, `Cache-Control: no-store`이며 쿠키 이름은 `__Host-chat_guest_v3`다. 쿠키 속성은 `HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=86400`이고 Domain은 지정하지 않는다. HTTPS/WSS 환경을 사용한다. HttpOnly 쿠키를 JavaScript로 읽거나 직접 생성하지 않는다.

응답 JSON은 기존 명시적 토큰 방식과의 호환성을 위해 아래 형식을 유지한다. 쿠키 방식에서는 `guest_token`을 저장하거나 사용하지 않는다.

```json
{"status":200,"msg":"OK","data":{"guest_token":"서버 발급 토큰"}}
```

유효한 쿠키가 있으면 동일한 토큰을 재사용한다. 쿠키가 없거나 만료·무효이면 새 토큰을 발급한다. 여러 탭의 최초 동시 발급을 줄이려면 Web Locks API 등으로 발급 요청을 직렬화한다. React 재렌더마다 발급하거나 연결하지 않는다.

## 2. WebSocket 연결

발급 응답을 받은 뒤 `/api/live-map/v3/chat/ws`에 연결하고 10초 안에 다음 첫 메시지를 보낸다.

```json
{"type":"guest","session":"cookie"}
```

브라우저가 해당 WebSocket 호스트에 적용되는 쿠키를 연결 요청에 자동으로 보낸다. 백엔드는 쿠키를 검증해 세션별로 연결 제한을 적용한다. `session: "cookie"`를 명시하면 쿠키가 누락된 경우에도 IP 기준으로 돌아가지 않고 `401 / CHAT_GUEST_SESSION_INVALID`를 반환한다.

```ts
const socket = new WebSocket(`${wsOrigin}/api/live-map/v3/chat/ws`);
socket.addEventListener('open', () => {
  socket.send(JSON.stringify({ type: 'guest', session: 'cookie' }));
});
```

기존 snapshot과 이벤트 처리를 유지한다. 여러 탭과 재연결은 쿠키를 공유하며 세션별 연결 시도는 분당 20회, 동시 연결은 최대 5개다. 로그인 시에는 기존 연결을 닫고 `{ "type": "auth", "token": "..." }` 방식으로 다시 연결한다.

## 3. Next.js 및 도메인 구성

**쿠키 발급 요청과 WebSocket 요청의 브라우저 기준 호스트가 같아야 한다.** 이 쿠키는 발급 호스트에만 적용된다. 권장 구성은 같은 사이트의 API 호스트에 브라우저가 직접 발급 요청과 WSS 연결을 보내거나, 두 요청 모두 프론트와 같은 호스트의 게이트웨이를 이용하는 것이다.

- HTTPS 프론트와 HTTPS API가 같은 사이트의 서로 다른 서브도메인인 경우에도 fetch에 `credentials: 'include'`를 설정한다. API CORS는 실제 프론트 Origin을 명시하고 자격 증명을 허용해야 한다.
- 현재 저장소의 공통 CORS는 `allow_origins=["*"]`다. 쿠키가 없는 브라우저의 첫 cross-origin 발급 요청에 필요한 CORS 구성을 보장하지 않는다. 직접 API를 호출하는 배포에서는 실제 프론트 Origin에 맞춘 CORS 설정이 필요하다. 이 변경에서 공통 legacy CORS는 수정하지 않았다.
- Next.js Route Handler가 발급 API를 대신 호출하면 방문자의 Cookie를 백엔드로 전달하고 백엔드의 Set-Cookie를 브라우저 응답으로 전달한다. Node 서버 내부 fetch만으로 브라우저 쿠키가 저장되지는 않는다.
- 프론트 호스트에서 쿠키를 발급받고 별도 API 호스트로 직접 WSS 연결하면 쿠키가 전달되지 않는다. 발급과 WSS 호스트를 맞춘다. 일반 Next.js Route Handler만으로 WebSocket 중계를 제공한다고 가정하지 않는다.
- 서로 다른 사이트의 도메인이나 localhost에서 운영 API를 호출하는 구성은 현재 `SameSite=Lax` 쿠키 방식으로 지원하지 않는다. 동일 사이트의 HTTPS 테스트 환경을 사용한다.
- SSR 서버 전역 변수, 공유 캐시, 로그에 토큰을 저장하지 않는다. 발급 요청·응답을 캐시하지 않는다.

쿠키의 host-only, HttpOnly 및 credentials 동작은 [MDN Set-Cookie 문서](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie)를 참고한다.

## 4. 만료와 오류 처리

| 상태 / 코드 | 프론트 처리 |
|---|---|
| 401 `CHAT_GUEST_SESSION_INVALID` | 발급 API를 다시 호출하고 재연결. 반복 실패하면 쿠키 저장·전달 문제로 표시하고 재연결 루프를 중단 |
| 429 `CHAT_CONNECT_RATE_LIMITED` | 연결 제한 안내. WS `retry_after` 초 이상 기다린 뒤 재연결. 새 세션 발급으로 우회하지 않음 |
| 429 `CHAT_CONNECTION_LIMIT` | 다른 탭을 닫거나 기다리도록 안내. 서버 대기 시간 반영 |
| 503 `CHAT_GUEST_SESSION_UNAVAILABLE` | 세션 서비스 연결 오류. 지수 backoff와 jitter로 재시도 |
| `SESSION_REFRESH_REQUIRED`, close 1012 | 기존 쿠키를 유지하고 발급 API를 거쳐 재연결 |

Redis 토큰은 최초 발급 후 24시간 만료이며 재사용으로 만료가 연장되지 않는다. 쿠키의 Max-Age는 발급 API 응답에서 다시 설정되므로 서버 토큰이 쿠키보다 먼저 만료될 수 있다. 이때 발급 API가 토큰을 교체한다. 만료 자체로 이미 열린 연결을 강제 종료하지는 않는다.

연결 오류를 ‘메시지를 너무 빠르게 보내고 있습니다’로 표시하지 않는다. 서버의 대기 시간을 사용하고 1초로 고정하지 않는다. 모집 채팅 연결 오류를 파티 패널에도 중복 표시하지 않는다. 프론트 페이지 안에서는 채팅 연결을 재사용한다.

## 5. 전환과 범위

백엔드 배포 후 프론트가 위 쿠키 모드를 사용하도록 배포한다. 예전 `{ "type": "guest" }` 메시지는 쿠키가 있으면 쿠키를 사용하고, 쿠키가 없으면 호환성을 위해 기존 IP 기준을 유지한다. 기존 `guest_token` 첫 메시지도 지원한다. 신규 프론트는 `session: "cookie"`를 명시한다.

익명 사용자는 기존처럼 모집 채팅 읽기만 가능하다. 파티 가입·초대·메시지 전송 권한을 주지 않으며 공개 접속자 목록에 익명 사용자를 추가하지 않는다. 파티 UI가 모집 채팅 연결 상태를 공유하는 경우 같은 연결을 재사용한다.

쿠키는 사람이나 계정을 식별하는 정보가 아니다. 시크릿 창, 쿠키 삭제, 다른 브라우저는 별도 세션이다. 공개 API에서 세션을 새로 발급받는 대량 공격까지 이 제한으로 막지는 않는다. 대량 발급·연결 제한은 인프라에서 별도로 적용한다.

## 확인 항목

- 처음 방문한 비로그인 브라우저에서 발급 응답의 쿠키가 저장되고 WS snapshot을 받는지 확인한다.
- 같은 브라우저의 새 탭·재연결은 같은 세션을 사용하고, 별도 시크릿 창은 별도 세션을 사용하는지 확인한다.
- 쿠키가 누락된 신규 모드는 401로 종료되고 IP 기준으로 연결되지 않는지 확인한다.
- 연결 제한 오류의 retry_after, 로그인·로그아웃 전환, 24시간 만료 후 재발급을 확인한다.
