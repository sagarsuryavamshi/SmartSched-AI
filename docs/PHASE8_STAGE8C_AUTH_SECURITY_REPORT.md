# SmartSched AI — Phase 8, Milestone 8C: Authentication & Role-Based Authorization Report

**Date:** November 26, 2026  
**Status:** Successfully Implemented & Certified  
**Framework:** FastAPI + OAuth2 with Password Flow & Bearer Tokens + HttpOnly Cookies  
**Hashing Engine:** passlib with bcrypt (12 rounds)  
**Token Standard:** JSON Web Signature (JWS/JWT) with HMAC-SHA256 (`HS256`)  

---

## 1. Authentication Architecture

SmartSched AI implements an administrative and academic observer security model:
- **No Plaintext Passwords:** Strict salted bcrypt hashing.
- **Session Tokens:** 24-hour expiration tokens containing user identity and role scope.
- **Dual Transport:** 
  1. Header: `Authorization: Bearer <token>` for API clients, CI/CD scripts, and Next.js async calls.
  2. Cookie: `smartsched_auth_token` with `HttpOnly` and `SameSite=Lax` for browser-native requests.
- **Generic Error Responses:** Prevent username enumeration on invalid authentication attempts (HTTP 401: *"Incorrect username or password"*).

---

## 2. Role-Based Access Control (RBAC) Matrix

| Endpoint Group | Action | Administrator (`admin`) | Observer / Student (`viewer`) | Unauthenticated |
| :--- | :--- | :---: | :---: | :---: |
| `/api/v1/auth/login` | Authenticate | Allowed | Allowed | Allowed |
| `/api/v1/auth/me` | Fetch Profile | Allowed | Allowed | 401 Unauthorized |
| `/api/v1/auth/users` | Manage Accounts | Allowed | **403 Forbidden** | 401 Unauthorized |
| `/api/v1/resources/*` (GET) | View Resources | Allowed | Allowed | Allowed |
| `/api/v1/resources/*` (POST/PUT/DEL)| Modify Resources | Allowed | Protected | Protected |
| `/api/v1/optimize/*` | Run Optimization | Allowed | Protected | Protected |
| `/api/v1/rescheduling/commit` | Apply Reschedule | Allowed | **403 Forbidden** | Protected |
| `/api/v1/rescheduling/rollback` | Rollback Reschedule | Allowed | **403 Forbidden** | Protected |
| `/api/v1/timetable/active` | View Timetable | Allowed | Allowed | Allowed |
| `/api/v1/analytics/*` | View Analytics | Allowed | Allowed | Allowed |

---

## 3. Verified Accounts for Acceptance Testing

- **Administrator Account:** `admin` / `Admin@SmartSched2026` (Full operational privileges)
- **Academic Observer Account:** `viewer` / `Viewer@SmartSched2026` (Read-only timetable and analytics access)
