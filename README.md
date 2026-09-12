# Offline Inventory Management System

A fully offline Windows desktop inventory management application. No internet connection, no cloud services — all data is stored locally on the machine it runs on.

Built with **Python 3.11+ · PySide6 (Qt) · SQLAlchemy · SQLite · Alembic · ReportLab · openpyxl · PyInstaller**.

## Features

### Master Data
- **Products** — SKU, barcode, name, category, unit, prices, reorder level, location, active/inactive status (never hard-deleted once it may have transaction history — deactivated instead)
- **Categories, Units, Locations** — simple reference data with add/rename/delete
- **Suppliers** and **Customers** — contact details for purchases and sales

### Inventory & Transactions
- **Purchase / Stock In** — multi-line purchases against a supplier, each line updating stock
- **Stock Out / Sale** — multi-line sales against a customer, blocked from taking any product negative
- **Stock Adjustment** — manual correction with a mandatory reason (physical count reconciliation)
- **Stock Ledger** — a complete, immutable, per-product movement history; the ledger is the source of truth, not just the cached stock count
- All stock-affecting operations run inside a single database transaction — a failure partway through a multi-item purchase/sale leaves **no partial data**, verified by automated tests

### Dashboard & Reporting
- Dashboard KPIs: active product count, total stock value, low-stock count, out-of-stock count, recent stock movements
- Reports: current stock, low stock, out-of-stock, and date-ranged stock movement — each exportable to **PDF** or **Excel**

### Security & Users
- Login required; passwords hashed with PBKDF2-SHA256 and a per-user random salt (never stored in plaintext)
- Four roles with different screen access: **Admin**, **Manager**, **Operator**, **Viewer**
- Full **audit log** of logins, user changes, deletions, activations, and stock adjustments
- First-run setup wizard creates the initial administrator account

### Local Data & Backup
- **Fully offline** — the app never makes a network call; the database lives in a folder you choose (or a sensible default), never inside the install directory
- First-run dialog to choose (or accept the default) database location, with automatic detection of an existing database at that location
- Automatic daily backup (configurable retention count) plus a manual "Backup Now"
- Restore from any previous backup, with an integrity check before restoring
- Database location and backup folder can both be changed later from the admin-only **Application Settings** screen

### Schema Migrations
- Real Alembic-based schema migrations run automatically on startup — a fresh install gets the full schema created from nothing, and a database from an older version of the app is upgraded in place, never re-created

### Packaging & Installation
- Packaged as a single Windows executable with PyInstaller
- **Self-installing**: double-clicking `InventoryManager.exe` the first time installs it properly — copies itself to `%LocalAppData%\Programs\...`, registers a Control Panel / Settings → Apps entry, adds a Start Menu shortcut (searchable via Windows Search), then relaunches from the installed copy. Every later launch just runs normally. Uninstalling from Control Panel removes everything cleanly.
- An Inno Setup installer script (`installer.iss`) is also provided as an alternative distribution path

### Design
- Modern web-style admin dashboard UI: dark sidebar navigation with icons, a header bar, card-based content panels with real drop shadows, and a consistent color palette across every screen

## Getting Started (Development)

```powershell
git clone https://github.com/P-Sudhakar-tech/offline_inventory_project.git
cd offline_inventory_project
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python main.py
```

Or use the included `run_app.bat` after setting up the virtual environment.

On first launch you'll be asked where to store the database, then to create an administrator account, then you can log in.

## Running Tests

```powershell
.venv\Scripts\python -m pytest tests/ -v
```

71+ unit tests cover the stock ledger, master data validation, transactions, reports, authentication, audit logging, database migrations, backup/restore, and hardening (boundary values, transaction atomicity, performance).

## Building the Windows Package

```powershell
.venv\Scripts\python -m PyInstaller inventory_manager.spec --noconfirm
```

This produces `dist\InventoryManager\InventoryManager.exe` — a self-installing executable (see Features above). To also build the optional Inno Setup installer:

```powershell
iscc installer.iss
```

## Project Structure

```
app/
├── config/        # Database location & app settings (JSON config)
├── data/          # SQLAlchemy models, session/engine, Alembic migrations
├── reports/       # PDF and Excel export helpers
├── security/      # Current-user session context
├── services/      # Business logic: master data, transactions, ledger, auth, audit, backup, reports
├── setup/         # Self-install / self-uninstall logic for the packaged exe
└── ui/            # PySide6 windows, dialogs, and tabs
tests/             # pytest test suite
main.py            # Application entry point
inventory_manager.spec   # PyInstaller build spec
installer.iss      # Inno Setup installer script (optional alternative)
```

## Roles & Permissions

| Screen | Admin | Manager | Operator | Viewer |
|---|:---:|:---:|:---:|:---:|
| Dashboard | ✅ | ✅ | ✅ | ✅ |
| Products | ✅ | ✅ | ✅ | |
| Categories / Units / Locations | ✅ | ✅ | | |
| Suppliers / Customers | ✅ | ✅ | | |
| Purchase / Sale / Adjustment | ✅ | ✅ | ✅ | |
| Stock Ledger | ✅ | ✅ | ✅ | ✅ |
| Reports | ✅ | ✅ | ✅ | ✅ |
| Users | ✅ | | | |
| Audit Log | ✅ | | | |
| Application Settings | ✅ | | | |

## License

MIT — see [LICENSE](LICENSE).
