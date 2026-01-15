# 🎯 Smart Blind Assistant - Dansk Guide

## Hurtig Start | Quick Start Guide

### Trin 1: Hent og installer Docker
```bash
# Installer Docker og Docker Compose
# https://docs.docker.com/get-docker/
```

### Trin 2: Start systemet
```bash
# I projektmappen
docker-compose up --build

# Vent til du ser: "Uvicorn running on http://0.0.0.0:8000"
```

### Trin 3: Åbn grænsefladen
```
http://localhost:8000/client/
```

### Trin 4: Vælg Dansk som sprog
- Tryk på **"🇩🇰 Dansk"** knappen
- Systemet vil hilse på dig på dansk

---

## Stemmekommandoer | Voice Commands

| Dansk | English | Funktionalitet |
|-------|---------|-----------------|
| "Hvad ser du" | "What is in front" | Beskriv scenen |
| "Læs" | "Read text" | Læs tekst fra skærm |
| "Vær stille" | "Quiet" | Aktivér stilletilstand |
| "Scan omkring" | "Full scan" | Fuld miljøscanning |

---

## Keyboard Shortcuts | Tastaturgenveje

| Tast | Funktion |
|------|----------|
| **Mellemrum** | Tryk for at tale / Slip for at sende |
| **Q** | Skift stilletilstand (quiet mode) |
| **D** | Beskriv scenen |

---

## Problemløsning | Troubleshooting

### Problem 1: "Kan ikke få adgang til kamera"
**Løsning:**
- Godkend kameraadgang i browserindstillinger
- Tryk på låseikonet i adresselinjen
- Vælg "Tillad" for kamera

### Problem 2: "Lyden virker ikke"
**Løsning:**
- Kontroller at lyd er tændt på din enhed
- Kontroller indstillinger i browser
- Prøv at genstarte containeren: `docker-compose restart`

### Problem 3: "Langsom respons"
**Løsning:**
- Første anmodning tager længere tid (indlæsning af modeller)
- Hvis du har GPU: Aktiver CUDA i docker-compose.yml
- Prøv at reducere billededstørrelse

### Problem 4: "Forbindelse nægtet"
**Løsning:**
```bash
# Kontroller at Docker kører
docker ps

# Genstarter alle services
docker-compose down
docker-compose up --build
```

---

## System Arkitektur | System Architecture

```
┌─────────────────────────────────────────┐
│   Browser / Web Interface (HTML/JS)      │
│   Dansk, Engelsk, Arabisk               │
└──────────────────┬──────────────────────┘
                   │
                   ↓ WebSocket/HTTP
┌─────────────────────────────────────────┐
│   FastAPI Application (Python)           │
│   - Assistant (Brain)                    │
│   - Vision (YOLO-World, OCR)            │
│   - Audio (Whisper, TTS)                │
│   - Navigation & Spatial Awareness      │
└──────────────────┬──────────────────────┘
                   │
        ┌──────────┼──────────┐
        ↓          ↓          ↓
    ┌────────┐ ┌──────┐ ┌─────────┐
    │ Models │ │  DB  │ │ Storage │
    │ YOLO   │ │PgSQL │ │ MinIO   │
    │Whisper │ │      │ │         │
    └────────┘ └──────┘ └─────────┘
```

---

## API Dokumentation | API Documentation

### Base URL
```
http://localhost:8000
```

### Vigtige Endpoints | Important Endpoints

#### Chat med Assistenten | Chat with Assistant
```
POST /assistant/chat
Content-Type: multipart/form-data

Parameters:
- audio: WAV fil
- image: Base64 billede (valgfrit)

Response:
- audio: WAV svar
- text: Beskedtekst
```

#### Stil Kommando | Issue Command
```
POST /assistant/command
Content-Type: application/json

{
  "text": "Hvad ser du",
  "image_b64": "base64_encoded_image"
}

Response:
{
  "text": "Jeg ser..."
}
```

#### Analyse Scene Stille | Silent Analysis
```
POST /assistant/analyze
Content-Type: application/json

{
  "image_b64": "base64_encoded_image"
}

Response:
{
  "should_speak": boolean,
  "alerts": [...],
  "speak_message": "string"
}
```

---

## Konfiguration | Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/fastapi_agent

# Storage (MinIO)
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# LLM (Ollama)
OLLAMA_HOST=http://ollama:11434

# Dybde Modeller
NNPACK_MAX_THREADS=0
```

### Docker Compose Services
- **PostgreSQL:** Port 5432 (Database)
- **MinIO:** Port 9000 (Storage)
- **Ollama:** Port 11434 (LLM)
- **FastAPI:** Port 8000 (Main API)
- **N8N:** Port 5678 (Workflow)

---

## Avanceret Konfiguration | Advanced Configuration

### GPU Support
```yaml
# docker-compose.yml
fastapi:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

### Performance Tuning
```python
# app/utils/config.py
# Juster disse værdier efter dine behov:
INFERENCE_BATCH_SIZE = 1
MAX_IMAGE_SIZE = 640
TTS_SAMPLE_RATE = 22050
```

---

## Support / Hjælp

Hvis du oplever problemer:

1. Check logfilerne:
```bash
docker logs -f blind_assist_api
```

2. Besøg API dokumentation:
```
http://localhost:8000/docs
```

3. Tjek health status:
```bash
curl http://localhost:8000/health
```

---

**Sidst opdateret:** 2026-01-15
**Sproget:** 🇩🇰 Dansk | 🇬🇧 English | 🇸🇦 Arabic
