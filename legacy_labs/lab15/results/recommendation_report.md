# Multi-Tenant Recommendation Report

## Actual benchmark summary

| Strategy | Operation | Average seconds |
| --- | --- | ---: |
| document | list | 0.000826 |
| document | create | 0.002523 |
| document | analytics | 0.000559 |
| collection | list | 0.000510 |
| collection | create | 0.002978 |
| collection | analytics | 0.000310 |

## Document-level isolation
- Advantages: simpler operational model, one shared collection, easy tenant filtering, lower infrastructure overhead.
- Disadvantages: every query must include tenant_id, risk of accidental cross-tenant queries, more application-level enforcement responsibility.
- Query performance: efficient for moderate tenant sizes and mixed workload; best when cross-tenant data is usually queried together.
- Backup considerations: backups are easier to manage because everything is in one data set, but recovery must preserve tenant-scoped filtering discipline.
- Schema evolution: lower operational cost, but schema changes affect every tenant in the same collection.

## Collection-per-tenant isolation
- Advantages: better physical isolation, reduced chance of accidental cross-tenant access, easier tenant-specific maintenance and security boundaries.
- Disadvantages: more collections to manage, more operational complexity, higher storage and index costs.
- Query performance: very strong for single-tenant analytic workloads because scans are limited to one tenant's collection; may require more connection and management overhead.
- Backup considerations: tenant-by-tenant backup and restore are straightforward but require careful retention and collection-level operational automation.
- Schema evolution: more isolated but changes need careful rollout across each tenant's collection.

## Recommendation
- Use document-level isolation for the default SaaS model when tenants are smaller or data volumes are moderate, and a shared operational profile is acceptable.
- Use collection-per-tenant isolation for enterprise or compliance-sensitive tenants, workloads requiring stronger data boundaries, or cases where a single tenant's operational blast radius must remain isolated.
- The benchmark data in this repository should guide the final choice for each workload and customer tier.
