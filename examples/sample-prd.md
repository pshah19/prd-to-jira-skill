# PRD: Multi-Currency Expenses & Delegate Approvals

**Product:** Nimbus Expense (fictional expense management SaaS)
**Author:** Product Management (sample data — not a real product)
**Status:** Draft for engineering scoping

## 1. Overview

Nimbus Expense currently only supports expense submission and approval in a single
company-wide currency (USD). Our fastest-growing customer segment is mid-market
companies with distributed teams across Europe and APAC, and the #1 blocker cited in
sales loss reports is "no multi-currency support." Separately, our largest existing
customers have asked for **delegate approvals** — the ability for an approver to
temporarily hand off their approval queue to a backup while on leave, without sharing
credentials or losing an audit trail.

This PRD covers both: multi-currency expense submission/conversion, and delegate
approval workflows, because they touch overlapping parts of the approval pipeline and
we want engineering to sequence them as one connected effort rather than two separate
projects that collide mid-quarter.

## 2. Goals

- Let employees submit expenses in their local currency; approvers and finance always
  see the company's reporting currency alongside the original.
- Let an approver delegate their approval authority to another user for a bounded time
  window, with a clear audit trail of who actually approved what.
- Keep the existing single-currency approval flow working for customers who don't
  need multi-currency (no forced migration).

## 3. Non-goals / Out of scope

- Multi-currency **reimbursement payouts** (payroll/bank transfer currency) — this PRD
  only covers expense submission, conversion display, and approval. Payout currency
  conversion is a separate future project; do not generate tickets for it.
- Permanent approval-authority reassignment (that's a role change, already supported
  today via admin settings) — delegation here is explicitly temporary/time-boxed.
- Historical expense report currency backfill/reconversion.

## 4. Multi-Currency Expense Submission

**Problem:** Employees today must manually convert receipts to USD before submitting,
which is error-prone and slow, especially for teams outside the US.

**Requirements:**
- Expense submission form must let the employee pick a currency (defaulting to the
  currency inferred from their profile's home office location) and enter the amount
  in that currency.
- The system must fetch a daily FX rate from our existing third-party FX rate
  provider integration (already used by the Finance Reporting module) and store the
  rate used at time of submission, so historical reports don't drift if rates change
  later.
- Because the FX rate source is the same one Finance Reporting already integrates
  with, this work should reuse that existing rate-fetching service rather than
  standing up a second integration — check with the Finance Reporting service owners
  before building a new client.
- The expense list and detail views (web and mobile) must show both the original
  submitted amount/currency and the converted reporting-currency amount.
- If the FX provider is unavailable at submission time, the employee should still be
  able to submit; conversion should be computed asynchronously once the rate service
  recovers, and the approver should not be blocked from approving in the meantime
  (approve on original amount, backfill converted amount later).
- Company admins need a settings screen to enable/disable multi-currency for their
  org and to set the reporting currency (defaults to USD).

## 5. Delegate Approvals

**Problem:** When an approver goes on leave, their expense approval queue backs up
or gets rerouted informally (sharing logins), which fails our compliance audit
requirements.

**Requirements:**
- An approver can designate a delegate and a date range (start/end) during which the
  delegate can approve on their behalf.
- While a delegation is active, expenses routed to the original approver should also
  appear in the delegate's queue, clearly marked as "delegated from `<name>`."
- The audit trail for any expense approved by a delegate must record both the
  delegate (who clicked approve) and the original approver (whose authority was
  used), visible in the existing audit log view.
- Delegation setup depends on the approval routing engine knowing how to resolve "who
  can currently approve this expense" — this resolution logic needs to be built once
  and shared by both the normal routing path and the delegate path, not duplicated.
- Delegations must auto-expire at the end of the date range with no manual cleanup
  required, and the original approver should get a notification when their delegation
  starts and ends.
- Company admins need visibility into active delegations org-wide for audit purposes
  (a simple list view is sufficient for v1).

## 6. Notifications & Audit

- Existing notification service should be extended (not replaced) to cover: delegation
  started, delegation ending in 24h, delegation ended, expense approved by a delegate.
- Audit log entries for delegated approvals must be filterable/searchable the same way
  existing audit entries are today — this depends on the audit log schema being
  extended to include an optional "acted as delegate for" field before any delegated
  approval events can be written.

## 7. Reporting Impact

- Finance's monthly export must include both original and converted amounts per
  expense line, and must correctly attribute delegated approvals to the original
  approver of record (not the delegate) for compliance reporting, unless Finance's
  own compliance team says otherwise — flag this as an open question if the answer
  isn't in this doc (it isn't; treat as unresolved and note the risk).

## 8. Success Metrics

- Multi-currency: reduction in "wrong currency" support tickets; adoption rate among
  EMEA/APAC customers within 2 quarters.
- Delegate approvals: reduction in average approval queue age during PTO periods for
  pilot customers.

## 9. Rollout

- Both features should ship behind org-level feature flags, multi-currency and
  delegate approvals independently toggleable, since not all customers need both at
  once.
- Delegate approvals has a hard dependency on the shared approval-resolution logic
  described in Section 5; multi-currency does not depend on delegate approvals and
  could ship first if delegate approvals slips.
