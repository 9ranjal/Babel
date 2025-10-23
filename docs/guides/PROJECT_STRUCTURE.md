# 📁 Project Structure Overview

This document explains the organized folder structure of the Termcraft AI project.

---

## 🏗️ **Root Structure**

```
Project Simple/
├── README.md                    # Main project documentation
├── backend/                     # FastAPI Backend
├── frontend-cra-old/            # React Frontend
├── docs/                        # Documentation
├── scripts/                     # Utility Scripts
├── config/                      # Configuration Files
├── supabase/                    # Database
└── tests/                       # Test Files
```

---

## 📚 **Documentation (`docs/`)**

### **Status & Progress (`docs/status/`)**
- `PROJECT_STATUS.md` - Current implementation status and progress metrics

### **Guides & Tutorials (`docs/guides/`)**
- `QUICK_START.md` - Getting started guide
- `IMPLEMENTATION_GUIDE.md` - Detailed implementation guide
- `PERSONA_DETAILS.md` - Persona information for testing
- `APPLY_DEV_POLICIES.md` - Development policies and RLS setup
- `PROJECT_STRUCTURE.md` - This file

### **Architecture (`docs/architecture/`)**
- `ARCHITECTURE_DIAGRAM.md` - System architecture diagrams

---

## 🔧 **Scripts (`scripts/`)**

### **Database Migration (`scripts/migration/`)**
- `apply_migration_simple.py` - Apply database migrations
- `run_migration.sql` - SQL migration script
- `create_test_transaction.sql` - Create test transaction data

### **Testing (`scripts/testing/`)**
- `test_copilot_flow.py` - Test complete copilot flow
- `test_schema.py` - Test database schema
- `list_personas.py` - List and display personas

### **Setup (`scripts/setup/`)**
- `setup_backend.sh` - Backend environment setup
- `start_backend_5001.sh` - Start backend server
- `start_frontend_5000.sh` - Start frontend server
- `start_termcraft.sh` - Start both servers

---

## ⚙️ **Configuration (`config/`)**
- `package.json` - Root package configuration
- `package-lock.json` - Package lock file

---

## 🗄️ **Database (`supabase/`)**
- `migrations/` - Database migration files
  - `001_initial_schema.sql`
  - `002_seed_data.sql`
  - `003_dev_policies.sql`
  - `004_test_user.sql`
  - `005_transactions.sql`
  - `006_mvp_rls_bypass.sql`
  - `007_mvp_rls_fix.sql`

---

## 🧪 **Tests (`tests/`)**
- `__init__.py` - Test package initialization

---

## 🎯 **Usage Examples**

### **Run Migration Scripts**
```bash
# Apply database migrations
python scripts/migration/apply_migration_simple.py

# Create test transaction
psql -f scripts/migration/create_test_transaction.sql
```

### **Run Testing Scripts**
```bash
# Test complete flow
python scripts/testing/test_copilot_flow.py

# List personas
python scripts/testing/list_personas.py

# Test schema
python scripts/testing/test_schema.py
```

### **Run Setup Scripts**
```bash
# Setup backend
bash scripts/setup/setup_backend.sh

# Start backend
bash scripts/setup/start_backend_5001.sh

# Start frontend
bash scripts/setup/start_frontend_5000.sh

# Start both
bash scripts/setup/start_termcraft.sh
```

---

## 📋 **File Organization Benefits**

### **Clear Separation**
- **Documentation** is organized by type (status, guides, architecture)
- **Scripts** are organized by purpose (migration, testing, setup)
- **Configuration** files are centralized

### **Easy Navigation**
- Related files are grouped together
- Clear naming conventions
- Logical folder hierarchy

### **Maintainability**
- Easy to find specific files
- Clear ownership of different components
- Scalable structure for future additions

---

## 🔄 **Migration Notes**

### **Files Moved From Root**
- `PROJECT_STATUS.md` → `docs/status/PROJECT_STATUS.md`
- `IMPLEMENTATION_GUIDE.md` → `docs/guides/IMPLEMENTATION_GUIDE.md`
- `PERSONA_DETAILS.md` → `docs/guides/PERSONA_DETAILS.md`
- `QUICK_START.md` → `docs/guides/QUICK_START.md`
- `APPLY_DEV_POLICIES.md` → `docs/guides/APPLY_DEV_POLICIES.md`
- `ARCHITECTURE_DIAGRAM.md` → `docs/architecture/ARCHITECTURE_DIAGRAM.md`

### **Scripts Organized**
- Migration scripts → `scripts/migration/`
- Testing scripts → `scripts/testing/`
- Setup scripts → `scripts/setup/`

### **Configuration Centralized**
- Package files → `config/`

---

## 🚀 **Next Steps**

1. **Update References**: Update any hardcoded paths in scripts
2. **Documentation**: Update internal links in documentation
3. **CI/CD**: Update build scripts to use new paths
4. **Team Onboarding**: Share this structure with team members

---

**Last Updated:** December 2024  
**Structure Version:** 1.0
