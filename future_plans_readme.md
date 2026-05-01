# Future Plans for Cloud Control Plane

This document captures the next-phase design and implementation goals for the cloud-managed control plane, to be read when the cloud portion of the project is built.

## Purpose

This project is currently a Raspberry Pi edge appliance running a self-contained local shop runtime.
The cloud control plane is a future extension, not required for current production operation.
It exists to provide optional centralized registration, health monitoring, remote configuration, and rollout control without breaking the existing local shop workflow.

## Current Production Branch

Core behavior today:
- Raspberry Pi runs a Flask-based local shop server.
- The device handles barcode scanning, license validation, staff dashboards, and shop operations locally.
- Local runtime state, configuration, and shop data remain on the device.
- The packaging flow is edge-focused and does not include a cloud service.

Key properties:
- offline-first local operation
- shop continuity even without network access
- no cloud dependency in the packaged edge runtime

## New Cloud Control Plane Branch

The cloud branch introduces an optional control plane layered on top of the existing edge appliance:

- edge device registration to a cloud controller
- periodic heartbeat/status reporting
- shared payload contracts for registration and health messages
- optional future config or rollout directives from cloud to edge

Important distinctions:
- the edge app remains the primary runtime; the cloud is additive and opt-in
- the cloud placeholder is a separate service, not part of the edge packaging
- shared contracts live in `shared/` so edge and cloud remain aligned
- current implementation is a proof-of-concept placeholder, not a production GCP deployment

## Build Goals for Cloud Part

When the cloud part is built, the focus should be on these capabilities:

1. Cloud-native control plane service
   - device registration endpoint
   - heartbeat endpoint
   - health and metadata status
   - secure authentication and device identity
   - mandatory monthly cloud license clearance
   - cloud is the authoritative license controller for periodic refresh
   - local license remains valid only when cloud clearance is successful

2. Shared schema and contract stability
   - keep request/response payload definitions in `shared/schemas.py`
   - version contracts carefully so edge and cloud remain compatible

3. Edge opt-in behavior
   - add cloud client in `src/control_plane_client.py`
   - use local runtime settings and `PACKAGE_SHOP_*` overrides
   - preserve existing local-only behavior unless cloud is enabled

4. Packaging and deployment separation
   - maintain `api_server.spec` for edge packaging only
   - introduce separate packaging or deployment plan for cloud service later
   - do not force cloud code into the edge runtime bundle

## What to Read on Antigravity

Read this file when you are ready to move from the placeholder proof-of-concept to the real cloud control plane build.
It should be used as a high-level checklist for architecture decisions, branch separation, and the minimum viable cloud service contract.

## Future Topics

Future work can include:
- real GCP deployment with Cloud Run / Firestore or equivalent
- remote configuration and feature rollout control
- cloud dashboard for fleet monitoring
- secure edge-cloud authentication and key rotation
- telemetry and cloud-driven incident alerts
