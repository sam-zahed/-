# 🎯 Smart Blind Assistant (Smart Blind Assistant)

![Status](https://img.shields.io/badge/Status-Active-success)
![Docker](https://img.shields.io/badge/Docker-Supported-blue)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)

Et fuldt integreret kunstig intelligens-projekt til at hjælpe blinde mennesker. Systemet kører lokalt (Offline) for at sikre privatlivsbeskyttelse og hastighed.

## ✨ Vigtigste funktioner

1.  **Samlet stemme-interface (Unified Audio Interface):**
    - Alt er integreret på en enkelt side `/client`.
    - En stor knap til at tale.
    - Fuldt support for stemmekommandoer ("Hvad ser du", "Læs", "Vær stille").

2.  **Avanceret kunstig intelligens:**
    - **YOLO-World:** Detekter hvad som helst (Open Vocabulary Object Detection).
    - **OCR:** Læs arabisk og engelsk tekst præcist.
    - **Depth Estimation:** Estimér afstande for at advare brugeren om forhindringer.
    - **Motion Detection:** Advarer kun brugeren ved bevægelse for at reducere forstyrrelser.

3.  **Multilingval support:**
    - 🇸🇦 Arabisk
    - 🇬🇧 Engelsk
    - 🇩🇰 Dansk

4.  **Nem at køre (Docker):**
    - En enkelt kommando starter alt.
    - Løser afhængigheds- (Dependencies) og lydproblemer.

---

## 🚀 Hurtig start

### 1. Brug Docker (Nemmeste og bedste)

```bash
# 1. Byg og start containerne
docker-compose up --build
```

Vent på meddelelsen: `Uvicorn running on http://0.0.0.0:8000`.

### 2. Brug

Åbn din browser på:
👉 **[http://localhost:8000/client/](http://localhost:8000/client/)**

- Vælg sproget.
- Tryk på skærmen og tal med assistenten.

---

## 🛠️ Projektstruktur

```
.
├── app/
│   ├── assistant/       # Brain og dialogstyring
│   ├── vision/          # Objektdetektering og OCR
│   ├── audio/           # Lydbehandling (ASR/TTS)
│   ├── main.py          # Startpunkt (FastAPI)
│   └── Dockerfile       # Container build fil
├── client/              # Brugergrænseflader (HTML/JS)
├── models/              # Modelmappe (downloades automatisk)
├── requirements.txt     # Påkrævede biblioteker
└── docker-compose.yml   # Docker konfiguration
```

---

## ❓ Fejlfinding

**1. Lyden virker ikke?**
- Sørg for, at lyden er aktiveret på din enhed.
- Sørg for, at browseren har "Autoplay" tilladelse til lyd.

**2. Kameraet virker ikke?**
- Sørg for, at browseren (Chrome/Firefox) har tilladelse til kameraadgang.
- Hvis du bruger HTTP (ikke HTTPS), kan nogle browsere blokere kameraet. (localhost er normalt tilladt).

**3. Langsomt svar?**
- Den første anmodning tager altid tid (for at indlæse modeller).
- Hvis du ikke har et grafikkort (GPU), kører systemet på processoren (CPU), hvilket er lidt langsommere, men virker.

---

## 📞 Kontakt
Dette projekt blev udviklet for at hjælpe blinde mennesker ved hjælp af de nyeste open source AI-teknologier.
