# SmartHire Frontend (basic, modular)

Same behavior as the earlier single-file version, split into the modules
from the original plan: `api/`, `auth/`, `pages/`, `components/`, `utils/`.
Adds real routing (`react-router-dom`) since the `auth/ProtectedRoute.jsx`
module only makes sense with it.

## Structure
```
src/
├── main.jsx                          # wraps App in BrowserRouter + AuthProvider
├── App.jsx                           # route table
├── api/
│   ├── client.js                      # shared fetch wrapper, attaches JWT
│   ├── auth.js                        # login()
│   ├── admin.js                       # getCandidates()
│   ├── candidate.js                   # getStatus()
│   └── interviewer.js                 # getAssignedCandidates(), submitDecision()
├── auth/
│   ├── AuthContext.jsx                # holds token/role/username
│   ├── useAuth.js                     # hook to read context
│   └── ProtectedRoute.jsx             # redirects if not logged in / wrong role
├── pages/
│   ├── LoginPage.jsx
│   ├── admin/AdminDashboard.jsx
│   ├── candidate/CandidateStatusPage.jsx
│   └── interviewer/AssignedCandidatesPage.jsx
├── components/
│   ├── StatusBadge.jsx
│   └── DataTable.jsx                  # generic table, columns can define custom render
└── utils/
    └── roleRoutes.js                  # role -> default landing path
```

## Setup
```
npm install
npm run dev
```
Runs on http://localhost:5173, expects backend at http://localhost:8000
(change `BASE_URL` in `src/api/client.js` if different).

## Test logins
| username     | password  | role        |
|--------------|-----------|-------------|
| admin1       | admin123  | admin       |
| candidate1   | cand123   | candidate   |
| interviewer1 | int123    | interviewer |

## Not included yet (add later)
- `hooks/useAntiCheat.js`, `hooks/usePolling.js` — no Q&A flow exists yet to attach them to
- JD create/edit form
- Candidate drill-down / evidence view
- Any real styling
