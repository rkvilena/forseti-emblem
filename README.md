 # Forsetiemblem

 Forsetiemblem is a Fire Emblem RAG application. It ingests chapter data from the Fire Emblem wiki, stores structured content in Postgres with pgvector embeddings, and serves a chat-focused UI that answers chapter questions using retrieval-augmented generation.

 ## Repository Structure

 - `backend/` — FastAPI service, ingestion pipeline, RAG retrieval, and data storage
 - `frontend/` — Next.js app with the chat UI, chapters list, and informational pages
 - `infrastructure/` — Docker Compose and Cloud Run deployment configs
 - `documentation/` — Project documentation
 - `start.sh` / `resetdb.sh` — Local helper scripts

## Documentation

- [Backend documentation](documentation/backend.md)
- [Frontend documentation](documentation/frontend.md)

## Disclaimer

Forseti Emblem is a non-commercial, open-source technical demonstration developed for portfolio and educational purposes.

- **Data source**: Textual content is retrieved from the [Fire Emblem Wiki](https://fireemblem.fandom.com/) via the MediaWiki API and is used under the terms of the CC BY-SA 3.0 license.
- **Ownership**: Fire Emblem and all associated characters, names, and lore are the intellectual property of Nintendo and Intelligent Systems. This project is not affiliated with, endorsed by, or sponsored by Nintendo or Intelligent Systems.
- **Purpose**: This repository showcases Retrieval-Augmented Generation (RAG) architecture and vector database implementation. It is not intended to replace official sources or to generate revenue.
- **Rights holders**: If you are a rights holder and have concerns regarding how this codebase or any live demonstration based on it uses your content, please reach out so we can discuss and address them appropriately. You can contact me at `rkvilena11@gmail.com` or via issues on the GitHub repository for this project.
