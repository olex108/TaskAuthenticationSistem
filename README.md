# TaskAuthenticationSistem

This project is a high-performance, stateless backend application implementing a fully custom Authentication and Authorization system built with **Django DRF** and **PostgreSQL**. 

---

## 🔐 Custom RBAC Architecture & Database Schema

The core requirement of this application is a custom access control model. This system implements a **Stateless Role-Based Access Control (RBAC)** strategy optimized for PostgreSQL.

### Database Schema Entity Relationship

The database tables are isolated from the framework and use customized entity mappings:

1. **`users`** (`User` model)
   * Core profile container. Stores hashed passwords using `pwdlib`.
   * Implements **Soft Delete**: accounts are never hard-deleted; instead, `is_active` is toggled to `False`.
2. **`roles`** (`Role` model)
   * High-level identity groups (e.g., `administrator`, `moderator`, `user`).
3. **`permissions`** (`Permission` model)
   * Atomic authorization codes reflecting specific system actions (e.g., `admin:access`, `mock:view_analytics`, `mock:edit_data`).
4. **`user_roles`** (M2M Junction Table)
   * Bridges Users to Roles. Enforces strict `unique_together` constraint to block duplicate records.
5. **`role_permissions`** (M2M Junction Table)
   * Bridges Roles to Permissions.

### Stateless Optimization (No-Database Jumps)
* **Access Tokens**: During the login phase (`LoginView`), the system compiles a flat list of all permissions the user possesses through their roles and injects this array directly into the short-lived JWT Access Token payload under the `permissions` claim.
* **Verification**: When a protected endpoint is called, `CustomJWTAuthentication` decodes the token. The custom `HasPermission` guard checks the user's rights **directly from the token memory**. The database is completely bypassed, eliminating heavy `JOIN` overheads on every HTTP request.
* **Soft-Delete Sync**: To instantly catch soft-deleted users without full model evaluation, the authentication layer runs an optimized `EXISTS` check against the `users` primary key table, which triggers immediate revocation.

### Stateful Session Control (Logout Revocation)
* **`refresh_tokens`** (`RefreshToken` model)
   * To prevent **Token Replay Attacks**, long-lived refresh tokens are recorded in the database. 
   * When a user calls `LogoutAPIView` or triggers a `UserSoftDeleteAPIView`, their active sessions are flagged with `is_logout=True` or deleted, preventing any future Access Token generation.

---

## 🛠 Features Implemented

* **User Lifecycle**: Registration (with custom complexity rules), Login, Profile Management (via ModelSerializers), and Soft Deletion.
* **Token Rotation**: Token reissue (`TokenRefreshView`) that destroys the old key and grants a new pair.
* **Timing-Attack Countermeasures**: Implements `dummy_verify` during login failure routines to balance database lookup response times and prevent email enumeration.
* **Isolated Environment**: A completely distinct application `business_mock` hosts mock strategic data endpoints protected by the RBAC guard.
* **Documentation**: Interactive OpenAPI 3.0 specification available via Swagger UI.

---

## 🚀 Getting Started (Installation & Deployment)

The deployment flow is highly streamlined. The application environment is managed using **Poetry**, and the infrastructure is orchestrated through **Docker Compose**. Local mirrors are integrated to guarantee bulletproof dependency downloads.

### Prerequisites
Make sure you have [Docker Desktop](https://docker.com) installed and running on your system.

### 1. Clone the Repository
Open your terminal and clone the project codebase:
```bash
git clone https://github.com/olex108/TaskAuthenticationSistem.git
```

### 2. Configure Environment Variables
Create a `.env` file in the root directory of the project and populate it with your local configuration parameters:
```env
SECRET_KEY=app_secret_key
DEBUG=app_debug_state
ALLOWED_HOSTS=list_of_hosts

# Postgres database params
DB_NAME=name_of_database
DB_USER=name_of_db_user
DB_PASSWORD=password
DB_HOST=host
DB_PORT=port
```

### 3. Build and Run via Docker Compose
Execute the orchestration command to pull the images, construct the isolated python runtime, and start up the services:
```bash
docker-compose up --build
```

**Automated Init Routines:**
When the container builds successfully, a chain of scripts executes sequentially thanks to database health checks:
1. Database migrations are applied to create the custom schema layout.
2. `seed_roles` command populates system defaults (`administrator`, `moderator`, `user` roles alongside atomic codes).
3. `create_admin` command configures a fallback administrator account.

---

## 📊 Testing the Application (Default Accounts)

Open your web browser and head to:
👉 **[http://127.0.0.1:8000/api/docs/#/](http://127.0.0.1:8000/api/docs/#/)**

### Interactive Verification Flow in Swagger UI:
1. Expand the `/api/auth/login/` block. Click **Try it out**.
2. Pass the automatically seeded admin credentials:
   ```json
   {
     "email": "admin@admin.com",
     "password": "admin"
   }
   ```
3. Execute the call. Copy the raw `access_token` from the JSON response object.
4. Scroll to the top of the page, click the **Authorize** button, paste the token, and lock it in.
5. You can now execute calls to protected business streams like `GET /api/business/analytics/` (which returns a `200 OK` mock report payload) or profile modifications. Any non-authorized user calling this routine will immediately hit a `401 Unauthorized` or `403 Forbidden` response boundary.
