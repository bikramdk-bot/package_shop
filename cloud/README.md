# Cloud Control Plane Placeholder

This directory is the starting point for the future Google Cloud control plane.

## Current scope

The placeholder app currently provides:
- `GET /control/health`
- `POST /device/register`
- `POST /device/heartbeat`

These endpoints are intentionally minimal. They exist to establish a shared contract between the Raspberry Pi edge runtime and the future cloud service.

## Shared contracts

Request and response payloads are defined in `shared/schemas.py`.

## Running locally

From the repository root:

```bash
python -m cloud.app.main
```

The placeholder server runs on port `8080`.

## Design constraints

- no parcel or customer operational data belongs here
- this service is for licensing, device registration, config distribution, health, and rollout control
- edge and cloud should continue sharing contracts from `shared/` until the architecture stabilizes