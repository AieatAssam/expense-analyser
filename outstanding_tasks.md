# Outstanding Tasks

The following capabilities described in the PRD are still incomplete or partially implemented in the codebase.

1. **AI Parsing Accuracy Validation Logic**
   - Implement full validation comparing line item totals with receipt total and confidence scoring.
   - Current status: partially implemented in `receipt_validation.py` but task `10.1` marked pending.
2. **Manual Editing Interface**
   - Build a complete front‑end editing workflow and hook it to backend APIs.
   - Existing React component `ReceiptEditModal.tsx` contains placeholder data.
3. **Approval Workflow and Bulk Operations**
   - Implement receipt approval status, bulk category assignment and bulk approval/rejection functions.
4. **Data Integrity Checks and Authorization**
   - Enforce strong validation for edits and ensure only authorised users can modify receipts.
5. **LLM Provider Integration** ✅
   - Implemented real API calls in `llm_openai.py` and `llm_gemini.py`.
6. **Auth0 JWKS Retrieval** ✅
   - JWKS fetched and cached in `auth.py` for JWT validation.
7. **Invitation Authorization Checks** ✅
   - Authorization enforced in `invitation.py` so only account owners or superusers can invite new users.
8. **WebSocket Backend for Real‑time Updates**
   - Frontend includes WebSocket logic but the API lacks matching WebSocket endpoints.
9. **Object Storage for Receipt Images**
   - Move receipt image storage from database binary columns to an object store as per PRD.

These tasks map to the pending items in `.taskmaster/tasks/tasks.json` and TODO comments in the source code.
