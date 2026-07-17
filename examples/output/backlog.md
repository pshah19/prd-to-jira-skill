# Backlog — Nimbus Expense: Multi-Currency & Delegate Approvals

Source PRD: `examples/sample-prd.md`

## Summary

- Epics: 5
- Tasks: 23
- Total story points: 78
- High-risk tasks: 4 (EPIC-1-2, EPIC-2-1, EPIC-5-2, EPIC-5-3)

## EPIC-1: Multi-currency expense submission & display

*Priority: High — 28 pts*

Let employees submit expenses in their local currency with automatic conversion to the company reporting currency, reusing the existing FX rate integration already used by Finance Reporting, so international teams stop hand-converting receipts.

### EPIC-1-1 · Extend expense data model & API to store original currency, amount, and FX rate used [Task, 5 pts, medium risk]

Add currency, original_amount, and fx_rate_used fields to the expense record and API so conversions don't drift if rates change later.

**Acceptance criteria:**
- Expense schema stores currency code, original amount, and the FX rate used at submission time
- API accepts and returns the new fields
- Existing single-currency (USD-only) expenses continue to work unchanged

**Depends on:** none
**Labels:** backend, expenses

### EPIC-1-2 · Integrate with existing Finance Reporting FX rate service client [Task, 5 pts, high risk]

Reuse the FX rate client already integrated for Finance Reporting rather than standing up a second integration; coordinate with Finance Reporting service owners on shared usage.

**Acceptance criteria:**
- Daily FX rate is fetched via the existing shared client, not a new integration
- Rate lookups are cached per day to avoid redundant calls
- Finance Reporting service owners have signed off on the shared usage pattern

**Depends on:** EPIC-1-1
**Labels:** backend, finance-reporting, integration

### EPIC-1-3 · Add async conversion fallback for when the FX provider is unavailable [Task, 5 pts, medium risk]

If the FX provider is down at submission time, allow submission to proceed and backfill the converted amount asynchronously once the rate service recovers.

**Acceptance criteria:**
- Submission succeeds even when the FX provider call fails
- A background job backfills the converted amount once the rate service is available again
- Expense record clearly reflects 'conversion pending' state until backfilled

**Depends on:** EPIC-1-2
**Labels:** backend, expenses

### EPIC-1-4 · Add currency selector and local-currency amount entry to web submission form [Story, 3 pts, low risk]

Employee can choose a currency (defaulting to their home-office currency) and enter the amount in that currency on the web app.

**Acceptance criteria:**
- Currency selector defaults to the employee's home-office currency
- Amount is submitted and stored in the selected currency
- Form validates amount > 0 for any supported currency

**Depends on:** EPIC-1-1
**Labels:** frontend, web

### EPIC-1-5 · Add currency selector and local-currency amount entry to mobile submission form [Story, 3 pts, low risk]

Same local-currency submission capability as the web form, on iOS/Android.

**Acceptance criteria:**
- Currency selector defaults to the employee's home-office currency
- Amount is submitted and stored in the selected currency
- Behavior matches the web form for parity

**Depends on:** EPIC-1-1
**Labels:** mobile

### EPIC-1-6 · Show original and converted amount on web expense list/detail views [Story, 2 pts, low risk]

Approvers and employees see both the originally submitted amount/currency and the converted reporting-currency amount.

**Acceptance criteria:**
- Expense list shows original currency amount with converted amount alongside it
- Expense detail view shows the FX rate used and submission date
- Pending-conversion state is visually distinct

**Depends on:** EPIC-1-2
**Labels:** frontend, web

### EPIC-1-7 · Show original and converted amount on mobile expense list/detail views [Story, 2 pts, low risk]

Mobile parity with the web list/detail view changes.

**Acceptance criteria:**
- Expense list shows original currency amount with converted amount alongside it
- Expense detail view shows the FX rate used and submission date

**Depends on:** EPIC-1-2
**Labels:** mobile

### EPIC-1-8 · Allow approvers to approve on original amount before conversion is backfilled [Task, 3 pts, medium risk]

Approvers should not be blocked from approving while the converted amount is still pending; converted amount backfills later without requiring re-approval.

**Acceptance criteria:**
- Approve action is available even when conversion is pending
- Backfilled conversion does not require re-approval
- Audit trail notes that approval occurred pre-conversion when applicable

**Depends on:** EPIC-1-3
**Labels:** backend, approvals

## EPIC-2: Shared approval-resolution engine & delegate setup

*Priority: High — 22 pts*

Build delegate approval setup on top of a single shared 'who can approve this expense right now' resolution service, used by both the normal and delegated routing paths, so delegation logic isn't duplicated or forked from the existing router.

### EPIC-2-1 · Build shared approval-resolution service for normal and delegate routing [Task, 8 pts, high risk]

Centralize 'who can currently approve this expense' logic into one service consumed by both the existing routing path and the new delegate path.

**Acceptance criteria:**
- Existing single-approver routing is refactored to call the new shared resolution service with no behavior change
- Service exposes a resolution API that delegate routing (EPIC-2-*) can also call
- Existing approval routing regression tests pass unchanged

**Depends on:** none
**Labels:** backend, approvals, platform

### EPIC-2-2 · Approver UI to designate a delegate and date range [Story, 3 pts, low risk]

An approver can pick a delegate and a start/end date during which the delegate can approve on their behalf.

**Acceptance criteria:**
- Approver can select any eligible delegate user
- Approver sets a start and end date for the delegation
- Delegation cannot be created with an end date before its start date

**Depends on:** EPIC-2-1
**Labels:** frontend, web

### EPIC-2-3 · Store delegation records with auto-expiry at end of date range [Task, 5 pts, medium risk]

Delegations auto-expire at the end of their date range with no manual cleanup step required.

**Acceptance criteria:**
- Delegation record includes delegator, delegate, start date, end date
- Delegation is automatically treated as inactive after its end date with no manual step
- No cleanup job leaves stale active delegations past their end date

**Depends on:** EPIC-2-1
**Labels:** backend

### EPIC-2-4 · Delegate's approval queue shows delegated-from expenses [Story, 3 pts, low risk]

While a delegation is active, expenses routed to the original approver also appear in the delegate's queue, clearly marked as delegated.

**Acceptance criteria:**
- Delegate sees delegated expenses in their own queue during the active window
- Each delegated item is labeled 'delegated from <name>'
- Items disappear from the delegate's queue once the delegation ends

**Depends on:** EPIC-2-1, EPIC-2-3
**Labels:** frontend, web

### EPIC-2-5 · Record both delegate (actor) and original approver (authority) on approval [Task, 3 pts, medium risk]

Every approval action taken by a delegate records who actually clicked approve and whose authority was used.

**Acceptance criteria:**
- Approval record stores acting user and authority-holder separately when they differ
- Non-delegated approvals are unaffected
- Data is available for the audit log work in EPIC-3

**Depends on:** EPIC-2-1
**Labels:** backend, compliance

## EPIC-3: Delegate notifications & audit trail

*Priority: Medium — 13 pts*

Extend the existing notification and audit systems to cover delegation lifecycle events and delegated-approval audit entries, meeting compliance requirements for who-approved-what visibility.

### EPIC-3-1 · Extend audit log schema with an optional 'acted as delegate for' field [Task, 3 pts, medium risk]

Audit log entries need to be able to represent a delegated approval before any delegated-approval events can be written.

**Acceptance criteria:**
- Audit log schema supports an optional delegate-authority field
- Existing non-delegated audit entries are unaffected
- Field is available for EPIC-3-2 to populate

**Depends on:** EPIC-2-1
**Labels:** backend, audit, compliance

### EPIC-3-2 · Write delegated-approval audit entries using the extended schema [Task, 2 pts, low risk]

Every delegated approval writes an audit entry populated with both the acting delegate and the original approver of record.

**Acceptance criteria:**
- Delegated approvals write an audit entry with both delegate and original approver
- Non-delegated approvals write audit entries as before, unaffected

**Depends on:** EPIC-3-1, EPIC-2-5
**Labels:** backend, audit

### EPIC-3-3 · Audit log view: filter/search delegated-approval entries [Story, 3 pts, low risk]

Delegated-approval audit entries are filterable and searchable the same way existing audit entries are today.

**Acceptance criteria:**
- Audit log UI can filter to delegated-approval entries specifically
- Search behavior matches existing audit entry search
- Both delegate and original approver are visible in the entry detail

**Depends on:** EPIC-3-2
**Labels:** frontend, web, audit

### EPIC-3-4 · Extend notification service for delegation lifecycle events [Task, 5 pts, medium risk]

Cover delegation started, delegation ending in 24h, delegation ended, and expense approved by a delegate, using the existing notification service.

**Acceptance criteria:**
- Original approver is notified when a delegation starts and ends
- Original approver is notified 24h before a delegation ends
- Notification is sent when an expense is approved by a delegate on their behalf

**Depends on:** EPIC-2-3
**Labels:** backend, notifications

## EPIC-4: Admin controls for rollout

*Priority: Medium — 7 pts*

Give company admins the settings and visibility needed to roll out both features safely: per-org multi-currency enablement, reporting currency, independent feature flags, and audit visibility into active delegations.

### EPIC-4-1 · Admin settings screen: enable/disable multi-currency and set reporting currency [Story, 3 pts, low risk]

Org admins can turn multi-currency on/off for their org and choose the reporting currency (default USD).

**Acceptance criteria:**
- Admin can toggle multi-currency on/off for their org
- Admin can set the org's reporting currency, defaulting to USD
- Change takes effect without requiring a deploy

**Depends on:** EPIC-1-1
**Labels:** frontend, web, admin

### EPIC-4-2 · Admin view: list active delegations org-wide [Story, 2 pts, low risk]

A simple list view for admins to see all currently active delegations across the org, for audit purposes.

**Acceptance criteria:**
- Admin can view all active delegations org-wide
- List shows delegator, delegate, and date range
- List updates as delegations expire

**Depends on:** EPIC-2-3
**Labels:** frontend, web, admin

### EPIC-4-3 · Independent org-level feature flags for multi-currency and delegate approvals [Task, 2 pts, low risk]

Both features ship behind separate org-level flags so customers can adopt either independently.

**Acceptance criteria:**
- Multi-currency and delegate approvals can be toggled independently per org
- Default state for both flags is off for existing orgs

**Depends on:** none
**Labels:** backend, platform

## EPIC-5: Finance reporting export updates

*Priority: Medium — 8 pts*

Update the monthly finance export to include original and converted expense amounts, and correctly attribute delegated approvals to the original approver of record for compliance — pending confirmation from Finance's compliance team on attribution rules.

### EPIC-5-1 · Add original and converted amount columns to the monthly finance export [Task, 3 pts, low risk]

Finance's export includes both the originally submitted amount/currency and the converted reporting-currency amount per line.

**Acceptance criteria:**
- Export includes original currency, original amount, and converted amount columns
- Existing single-currency export rows are unaffected

**Depends on:** EPIC-1-2
**Labels:** backend, finance-reporting

### EPIC-5-2 · Confirm export attribution rule for delegated approvals with Finance compliance [Spike, 2 pts, high risk]

PRD leaves open whether delegated approvals should attribute to the original approver or the delegate in compliance exports. Resolve with Finance's compliance team before building EPIC-5-3.

**Acceptance criteria:**
- Written decision from Finance compliance team on attribution rule
- Decision documented and linked from EPIC-5-3

**Depends on:** none
**Labels:** finance-reporting, compliance

### EPIC-5-3 · Update export attribution logic for delegated approvals per compliance decision [Task, 3 pts, high risk]

Implement the attribution rule decided in EPIC-5-2 in the export logic, using the delegated-approval audit data from EPIC-3-2.

**Acceptance criteria:**
- Export attributes delegated approvals per the confirmed compliance rule
- Export correctly distinguishes delegated vs. non-delegated approvals

**Depends on:** EPIC-5-2, EPIC-3-2
**Labels:** backend, finance-reporting, compliance

