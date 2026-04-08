# Connecting to PostgreSQL (Windows 11) from WSL2

## Prerequisites
- PostgreSQL installed and running on Windows 11
- WSL2 with mirrored networking mode (default on Windows 11)

---

## Step 1 — Configure PostgreSQL to accept external connections

Open `C:\Program Files\PostgreSQL\<version>\data\postgresql.conf` and set:

```conf
listen_addresses = '*'
```

---

## Step 2 — Allow WSL connections in pg_hba.conf

Open `C:\Program Files\PostgreSQL\<version>\data\pg_hba.conf` and add at the bottom:

```conf
host    all             all             192.168.0.0/16          scram-sha-256
```

---

## Step 3 — Restart PostgreSQL

`Win + R` → `services.msc` → find `postgresql-x64-<version>` → **Restart**

---

## Step 4 — Add a Windows Firewall rule

Open **PowerShell as Administrator** and run:

```powershell
New-NetFirewallRule -DisplayName "PostgreSQL WSL2" -Direction Inbound -Protocol TCP -LocalPort 5433 -Action Allow
```

> Replace `5433` with your PostgreSQL port if different.

---

## Step 5 — Get your Windows LAN IP

In PowerShell:

```powershell
ipconfig
```

Look for **IPv4 Address** under your active adapter (Ethernet or Wi-Fi). It will look like `192.168.x.x`.

---

## Step 6 — Test the connection from WSL

```bash
psql -h 192.168.x.x -p 5433 -U postgres -d your_db
```

> Install psql if not available: `sudo apt update && sudo apt install postgresql-client -y`

---

## Step 7 — Set the connection string in your app

In your `.env` file:

```env
POSTGRESQL_HOST=192.168.x.x
POSTGRESQL_PORT=5433
POSTGRESQL_DB_NAME=your_db
POSTGRESQL_PWD=your_password
```

In your code:

```python
CONNECTION = f"postgresql+psycopg://postgres:{POSTGRESQL_PWD}@{POSTGRESQL_HOST}:{POSTGRESQL_PORT}/{POSTGRESQL_DB_NAME}"
```

---

## Notes

- The LAN IP (`192.168.x.x`) can change if your network changes. If it does, update the `POSTGRESQL_HOST` in your `.env`.
- Do **not** use `localhost` or `127.0.0.1` — in WSL2 mirrored mode these do not reliably resolve to the Windows host.
- The `192.168.0.0/16` rule in `pg_hba.conf` covers the full LAN subnet so you won't need to update it when the IP changes.
