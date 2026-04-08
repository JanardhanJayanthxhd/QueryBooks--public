# API Reference

## Local Setup

### 1. Install pgvector

`pgvector` is a PostgreSQL extension that adds vector similarity search — required for storing and querying embeddings.

**Windows (using installer):**

Download the pre-built `.exe` for your PostgreSQL version from [github.com/pgvector/pgvector/releases](https://github.com/pgvector/pgvector/releases) and run it, **or** open **Stack Builder** (bundled with PostgreSQL) → Select your server → *Database Server Extensions* → tick `pgvector`.

**macOS (Homebrew):**

```bash
brew install pgvector
```

**Linux (apt):**

```bash
sudo apt install postgresql-16-pgvector  # replace 16 with your pg version
```

---

### 2. Create the `vector_db` database

The app connects to a database named `vector_db`. Run these commands in `psql` as a superuser:

```sql
-- Connect as superuser
psql -U postgres

-- Create the database
CREATE DATABASE vector_db;

-- Switch into it
\c vector_db

-- Enable the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Confirm it loaded
\dx
-- Should show: vector | ... | functions for vector statistics

-- Exit
\q
```

---

### 3. Configure credentials

Create `locals.json` in the project root:

```json
{
  "MainFunction": {
    "OPENAI_API_KEY": "sk-...",
    "POSTGRESQL_PWD": "your_postgres_password",
    "JWT_SECRET_KEY": "your_jwt_secret"
  }
}
```

The app connects as the `postgres` user on `localhost:5432`. If you use a different role or host, update `src/core/secrets/vector_db.py` and `src/core/constants.py` accordingly.

---

### 4. Run Alembic migrations

Migrations create the `user` and `user_llm_cache` tables. The `langchain_pg_embedding` and `langchain_pg_collection` tables are created automatically by `langchain-postgres` on first use.

```bash
alembic upgrade head
```

---

### 5. Start the server

```bash
uvicorn src.api.main:app --reload
```

---

## Architecture Overview

```mermaid
graph TD
    Client([Client])

    subgraph API ["FastAPI Application"]
        direction TB
        R_user["/user — Register / Login"]
        R_ai["/ai — Direct LLM Query"]
        R_chat["/chat — RAG Chat"]
        R_data["/data — Upload Documents"]
    end

    subgraph Core ["Core Internals"]
        JWT[JWT Auth]
        Cache[LLM Cache<br/>PostgreSQL]
        VDB[Vector Store<br/>PGVector]
        LLM[OpenAI<br/>gpt-4o-mini]
        Embed[Embeddings<br/>text-embedding-3-large]
    end

    DB[(PostgreSQL<br/>user<br/>user_llm_cache<br/>langchain_pg_embedding)]

    Client --> R_user
    Client --> R_ai
    Client --> R_chat
    Client --> R_data

    R_user --> DB
    R_ai --> LLM
    R_chat --> JWT --> DB
    R_chat --> Cache --> DB
    R_chat --> VDB --> DB
    R_chat --> LLM
    R_data --> JWT --> DB
    R_data --> Embed --> VDB
```

---

## Endpoints

### POST `/user/register`

Creates a new user. The password is hashed with Argon2 before being stored — the raw password never touches the database.

```mermaid
sequenceDiagram
    participant C as Client
    participant API as /user/register
    participant H as Argon2 Hasher
    participant DB as PostgreSQL

    C->>API: POST { name, email, password }
    API->>H: hash_password(password)
    H-->>API: password_hash
    API->>DB: INSERT INTO user (name, email, password_hash)
    DB-->>API: OK
    API-->>C: { response: "success" }
```

**Internals used:**
- `utility.hash_password()` — Argon2 hashing
- `User` ORM model — maps to the `user` table
- SQLAlchemy session via `Depends(get_db)`

---

### POST `/user/login`

Authenticates a user and returns a short-lived JWT.

```mermaid
sequenceDiagram
    participant C as Client
    participant API as /user/login
    participant DB as PostgreSQL
    participant JWT as JWT Module

    C->>API: POST { email, password }
    API->>DB: SELECT user WHERE email = ?
    DB-->>API: user row
    API->>API: verify_password(input, stored_hash)
    alt Password valid
        API->>JWT: create_access_token({ email, id })
        JWT-->>API: signed HS256 token (30 min TTL)
        API-->>C: { access_token: "..." }
    else Invalid
        API-->>C: 500 Authentication failed
    end
```

**Token payload:**
```json
{ "email": "user@example.com", "id": 1, "exp": 1234567890 }
```

**Internals used:**
- `utility.verify_password()` — Argon2 comparison
- `jwt.create_access_token()` — signs with HS256
- Secret key loaded from `locals.json` (dev) or AWS Secrets Manager (prod)

---

### POST `/ai/query`

A direct, unauthenticated LLM call. No documents, no retrieval — just a raw conversation with the model. Keeps an in-memory session history.

```mermaid
sequenceDiagram
    participant C as Client
    participant API as /ai/query
    participant Hist as In-Memory History
    participant LLM as OpenAI gpt-4o-mini

    C->>API: POST { query: "..." }
    API->>Hist: read current HISTORY
    API->>LLM: invoke(HISTORY + query)
    LLM-->>API: AIMessage (content + usage_metadata)
    API->>API: clean_llm_output(content)
    API->>API: calculate_token_cost(usage)
    API->>Hist: update_history(query, response)
    API-->>C: { ai response, token cost }
```

**Internals used:**
- `ai_utility.get_agent()` — initializes `ChatOpenAI(temperature=0)`
- `ai_utility.clean_llm_output()` — strips markdown artifacts
- `ai_utility.calculate_token_cost()` — computes cost from `usage_metadata`
- `ai_utility.update_history()` — appends `HumanMessage` + `AIMessage` to global `HISTORY`

---

### POST `/chat`  *(requires auth)*

The core RAG endpoint. Uses the user's uploaded documents as context. Results are cached per-user to avoid redundant LLM calls.

```mermaid
flowchart TD
    A[POST /chat with Bearer token] --> B[Authenticate JWT]
    B --> C{Token valid?}
    C -- No --> Z[401 Unauthorized]
    C -- Yes --> D[Check LLM Cache<br/>user_id + prompt + model]
    D --> E{Cache hit?}
    E -- Yes --> F[Return cached response<br/>~0ms]
    E -- No --> G[Contextualize question<br/>using chat history]
    G --> H[Vector similarity search<br/>k=10, filtered by user_id]
    H --> I[Format retrieved documents]
    I --> J[LLM generates answer<br/>with document context]
    J --> K[Save to cache<br/>user_llm_cache table]
    K --> L[Update in-memory HISTORY]
    L --> M[Return response<br/>with timing + token cost]
```

#### RAG Chain Internals

```mermaid
graph LR
    subgraph RAG ["Conversational RAG Chain"]
        direction TB
        CTX["Contextualize Chain<br/>─────────────────<br/>Rewrite question<br/>based on history<br/>using CONTEXTUALIZE_PROMPT"]
        RET["Retriever<br/>─────────────────<br/>PGVector similarity search<br/>k=10<br/>filter: user_id = current user"]
        QA["QA Chain<br/>─────────────────<br/>Answer from context only<br/>using QA_PROMPT<br/>gpt-4o-mini"]
    end

    History([Chat History]) --> CTX
    Query([User Query]) --> CTX
    CTX --> RET
    RET --> QA
    QA --> Answer([Answer])
```

**Cache key:** `(user_id, prompt_text, llm_model_name)`
**Retrieval filter:** embeddings are tagged with `user_id` at upload time, so users only retrieve their own documents.

**Internals used:**
- `jwt_utility.authenticate_user_from_token()` — FastAPI dependency, validates Bearer token
- `cache.get_cached_response()` — queries `user_llm_cache` table
- `ai_utility.get_conversational_rag_chain()` — builds the full LangChain pipeline
- `ai_utility.contextualized_retrival()` — rewrites question if history exists
- `secrets.vector_db` — singleton `PGVector` store instance
- `cache.save_to_cache()` — upserts result into `user_llm_cache`

---

### POST `/data/upload_pdf`  *(requires auth)*

Processes a PDF file into vector embeddings. Duplicate detection prevents re-embedding the same file.

```mermaid
flowchart TD
    A[POST /data/upload_pdf<br/>multipart PDF file] --> B[Authenticate JWT]
    B --> C{Token valid?}
    C -- No --> Z[401 Unauthorized]
    C -- Yes --> D{File extension<br/>= .pdf?}
    D -- No --> Y[415 Unsupported Media Type]
    D -- Yes --> E[SHA-256 hash<br/>of file bytes]
    E --> F{Hash exists in<br/>langchain_pg_embedding?}
    F -- Yes --> X[Return: already exists]
    F -- No --> G[Extract text<br/>PyMuPDF loader]
    G --> H[Split into chunks<br/>size=1000, overlap=200]
    H --> I[Attach metadata<br/>source, hash, user_id]
    I --> J[Generate embeddings<br/>text-embedding-3-large]
    J --> K[Store in PGVector<br/>langchain_pg_embedding]
    K --> L[Return success]
```

**Internals used:**
- `database_utility.check_existing_hash()` — raw SQL query on `langchain_pg_embedding.cmetadata`
- `database_utility.get_documents_from_file_content()` — reads bytes with `PyMuPDFLoader`
- `RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)`
- `database_utility.add_base_url_hash_user_id_to_metadata()` — injects `user_id`, `hash`, `source` into each chunk's metadata
- `PGVector.aadd_documents()` — async embedding + storage

---

### POST `/data/upload_web_content`  *(requires auth)*

Fetches a URL, extracts visible text, and stores it as embeddings — same pipeline as PDF.

```mermaid
flowchart TD
    A[POST /data/upload_web_content<br/>{ url }] --> B[Authenticate JWT]
    B --> C{Token valid?}
    C -- No --> Z[401 Unauthorized]
    C -- Yes --> D[SHA-256 hash of URL string]
    D --> E{Hash exists in<br/>langchain_pg_embedding?}
    E -- Yes --> X[Return: already exists]
    E -- No --> F[Fetch page content<br/>WebBaseLoader / BeautifulSoup]
    F --> G[Extract base URL<br/>remove fragments]
    G --> H[Split into chunks<br/>size=1000, overlap=200]
    H --> I[Attach metadata<br/>source URL, hash, user_id]
    I --> J[Generate embeddings<br/>text-embedding-3-large]
    J --> K[Store in PGVector]
    K --> L[Return success]
```

**Internals used:**
- `utility.hash_str()` — SHA-256 of URL string for deduplication
- `WebBaseLoader` (LangChain) — HTTP fetch + BeautifulSoup parsing
- Same chunking, metadata, and PGVector storage path as PDF upload

---

## Authentication Flow

Shared by `/chat` and `/data/*` endpoints.

```mermaid
sequenceDiagram
    participant C as Client
    participant Dep as authenticate_user_from_token()
    participant JWT as jwt.decode_access_token()
    participant DB as PostgreSQL

    C->>Dep: Request with Authorization: Bearer <token>
    Dep->>JWT: decode_access_token(token)
    JWT-->>Dep: payload { email, id } or JWTError
    alt Token invalid / expired
        Dep-->>C: 401 Unauthorized
    end
    Dep->>DB: SELECT user WHERE email = payload.email
    alt User not found
        Dep-->>C: 401 Unauthorized
    end
    Dep-->>Endpoint: User object
```

---

## Database Schema

```mermaid
erDiagram
    user {
        int id PK
        string name
        string email
        string password_hash
    }

    user_llm_cache {
        int idx PK
        int user_id FK
        string llm
        text prompt
        text response
    }

    langchain_pg_collection {
        uuid uuid PK
        string name
        json cmetadata
    }

    langchain_pg_embedding {
        uuid id PK
        uuid collection_id FK
        vector embedding
        string document
        json cmetadata
    }

    user ||--o{ user_llm_cache : "has cached responses"
    langchain_pg_collection ||--o{ langchain_pg_embedding : "contains"
```

> `langchain_pg_embedding.cmetadata` stores `{ user_id, source, hash }` — this is what filters retrieval per user and enables deduplication.
