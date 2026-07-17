# Dependency Map — Nimbus Expense: Multi-Currency & Delegate Approvals

Jira's CSV importer cannot create issue links on first import (ticket keys don't exist yet). Import `jira_import.csv` first, then use this list to add 'is blocked by' links by matching each Internal ID's Summary to the newly created Jira issue.

| Internal ID | Summary | Depends On | Risk |
|---|---|---|---|
| EPIC-1-1 | Extend expense data model & API to store original currency, amount, and FX rate used | — | medium |
| EPIC-1-2 | Integrate with existing Finance Reporting FX rate service client | EPIC-1-1 | high |
| EPIC-1-3 | Add async conversion fallback for when the FX provider is unavailable | EPIC-1-2 | medium |
| EPIC-1-4 | Add currency selector and local-currency amount entry to web submission form | EPIC-1-1 | low |
| EPIC-1-5 | Add currency selector and local-currency amount entry to mobile submission form | EPIC-1-1 | low |
| EPIC-1-6 | Show original and converted amount on web expense list/detail views | EPIC-1-2 | low |
| EPIC-1-7 | Show original and converted amount on mobile expense list/detail views | EPIC-1-2 | low |
| EPIC-1-8 | Allow approvers to approve on original amount before conversion is backfilled | EPIC-1-3 | medium |
| EPIC-2-1 | Build shared approval-resolution service for normal and delegate routing | — | high |
| EPIC-2-2 | Approver UI to designate a delegate and date range | EPIC-2-1 | low |
| EPIC-2-3 | Store delegation records with auto-expiry at end of date range | EPIC-2-1 | medium |
| EPIC-2-4 | Delegate's approval queue shows delegated-from expenses | EPIC-2-1, EPIC-2-3 | low |
| EPIC-2-5 | Record both delegate (actor) and original approver (authority) on approval | EPIC-2-1 | medium |
| EPIC-3-1 | Extend audit log schema with an optional 'acted as delegate for' field | EPIC-2-1 | medium |
| EPIC-3-2 | Write delegated-approval audit entries using the extended schema | EPIC-3-1, EPIC-2-5 | low |
| EPIC-3-3 | Audit log view: filter/search delegated-approval entries | EPIC-3-2 | low |
| EPIC-3-4 | Extend notification service for delegation lifecycle events | EPIC-2-3 | medium |
| EPIC-4-1 | Admin settings screen: enable/disable multi-currency and set reporting currency | EPIC-1-1 | low |
| EPIC-4-2 | Admin view: list active delegations org-wide | EPIC-2-3 | low |
| EPIC-4-3 | Independent org-level feature flags for multi-currency and delegate approvals | — | low |
| EPIC-5-1 | Add original and converted amount columns to the monthly finance export | EPIC-1-2 | low |
| EPIC-5-2 | Confirm export attribution rule for delegated approvals with Finance compliance | — | high |
| EPIC-5-3 | Update export attribution logic for delegated approvals per compliance decision | EPIC-5-2, EPIC-3-2 | high |

