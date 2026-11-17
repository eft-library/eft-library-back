# 3D 지도 종료 (2026-11-18)

공유 maps 모델과 행은 2D·라이브 지도·파티에서 계속 사용한다. 3D 전용 API `/api/map/v3/detail/{normalized_name}` 등록과 서비스 파일, ORM/DDL의 `three_image`, `three_json`만 제거했다. 종료된 API는 배포 후 404다. Airflow 자동완성 생성 SQL에서 `/map/...` 구문도 제거했다.

운영 DB 및 원격 파일 삭제는 실행하지 않았다. 프론트가 아직 제거 배포 중이므로 다음 순서로 적용한다.

1. 프론트 3D 호출/페이지 제거 배포.
2. 백엔드 변경 배포 및 Airflow `plugins/custom_module/queries/autocomplete.py` 배포.
3. `sql/migrations/20261118_retire_3d_maps.sql` 실행. 컬럼 2개와 3D 전용 자동완성·사이트맵·메뉴 링크를 제거한다. maps 행, `/map-of-tarkov`, `/live-map`, `/roadmap` 및 공통 지도 메뉴 그룹은 유지한다. 재실행 가능하며 CASCADE는 없다.
4. 스토리지 파일 목록을 확인하고 삭제한다.

```sh
.venv/bin/python scripts/retire_3d_map_assets.py
.venv/bin/python scripts/retire_3d_map_assets.py --execute
```

스크립트는 2026-11-18 운영 maps를 읽기 전용으로 조회하여 캡처한 manifest(`20261118_retire_3d_maps.assets.json`)의 정확한 18개 GLB만 대상으로 한다. 28개 지도 행이 이를 참조하고 있었으며 `prepare.glb` 등 중복 참조는 한 번만 삭제한다. 폴더 전체나 공통 이미지 파일은 삭제하지 않는다. DB 컬럼이 아직 남아 있으면 실제 삭제를 거절한다. 기존 `.env`의 `RUSTFS_ENDPOINT`, `RUSTFS_ACCESS_KEY`, `RUSTFS_SECRET_KEY`를 사용한다. 이미 없는 객체는 건너뛰며 중간 실패 시 재실행할 수 있다. 버전 관리가 설정된 버킷의 과거 버전 삭제 및 CDN 캐시 제거는 수행하지 않는다.

이 저장소에는 3D GLB 실파일이 없고 원격 object storage에 있다. 운영 SQL 실행 및 파일 삭제 후 프론트의 사이트맵·자동완성 캐시도 갱신한다. 프론트의 컴포넌트·공개 파일 정리는 프론트 작업에서 별도로 진행한다.
