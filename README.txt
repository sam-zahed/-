n8n Agent Package
==================
Files generated at: /mnt/data/n8n_agent_package

What is included:
- fastapi_service/ (app.py, requirements.txt, Dockerfile)
- docker-compose.yml  (starts postgres, minio, fastapi)
- deploy.sh (runs docker compose up -d --build)
- sql/schema.sql
- n8n_templates/ (three workflow JSON skeletons)

Quick start (assuming you already run n8n separately):
1. Copy this folder to your host or open a shell in the environment where Docker can run.
2. Run: ./deploy.sh
3. Open n8n (wherever you host it) and import the JSON templates in n8n_templates/ then edit Function nodes to add your real logic.
4. Point your device to the Ingest webhook path: <your-n8n-host>/webhook/ingest

Notes:
- The FastAPI app and n8n are designed to run on the same docker network (docker-compose) but n8n here is excluded because you indicated it's already running.
- Replace placeholder logic in app.py with your real model calls and database inserts.


---

## Additional: Ready-to-paste Function Node Snippets

Files are in `n8n_templates/function_snippets/`:
- Quick_Preprocess.js  -> Use inside a Function node after Webhook to set event_id, timestamp, and prepare upload options.
- Context_Merge.js    -> Use after calling the RT model to compute merged_confidence and decision hints.

## How to import and wire the workflows into your existing n8n (single-host setup)
1. Copy the `n8n_templates/*.json` files to your machine.
2. In n8n UI: Top-right -> Import -> paste JSON or upload the file. Import each workflow.
3. Edit the HTTP Request nodes to point to your FastAPI host (e.g., http://host.docker.internal:8000 or http://YOUR_FASTAPI_HOST:8000) depending on Docker networking.
4. For Function nodes that need to call HTTP (upload_tmp), replace the placeholder HTTP call in the snippet with a separate HTTP Request node in n8n that uses the options set in the Function node.
5. Ensure n8n can reach FastAPI and MinIO via network. If running n8n outside docker-compose, set FastAPI host to an IP accessible from n8n container (or run FastAPI on host network).

## Notes about running full stack vs using your current n8n
- The updated `docker-compose.yml` includes n8n so you can run the entire stack together (Postgres, MinIO, FastAPI, n8n). If you prefer to keep your existing n8n instance running separately, remove the `n8n` service from docker-compose or leave it commented, and make sure your existing n8n can reach the FastAPI service (http://<fastapi-host>:8000).

