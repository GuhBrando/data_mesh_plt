# Data Contract — Structured ODCS Form Design

**Date:** 2026-04-26  
**Branch:** feature/using-data-contract  
**Scope:** Core ODCS fields + tier classification wizard + YAML preview (UI/DB layer only)

---

## Context

The platform currently stores Data Contracts as a generic `obj: JSONB` blob with no enforced structure. The creation form is a raw JSON textarea. This design replaces that with a structured ODCS-compliant model covering core fields, a tier classification wizard, and a rendered YAML preview on the detail page.

Git sync, approval workflows, and consumer registration are explicitly out of scope for this iteration.

---

## Database

### Migration

Drop the `obj` column from `catalog.data_contracts`. Add the following columns:

| Column | Type | Constraint | Default |
|--------|------|------------|---------|
| `title` | `text` | `NOT NULL` | — |
| `version` | `text` | `NOT NULL` | `'1.0.0'` |
| `owner` | `text` | `NOT NULL` | — |
| `domain` | `text` | `NOT NULL` | — |
| `tier` | `int` | `NOT NULL, CHECK (tier BETWEEN 1 AND 4)` | — |
| `status` | `text` | `NOT NULL, CHECK (status IN ('draft', 'in_review', 'active', 'deprecated'))` | `'draft'` |
| `models` | `jsonb` | `NOT NULL` | `'{}'` |
| `servicelevels` | `jsonb` | `NOT NULL` | `'{}'` |

### Indexing rationale

No indexes on `tier` or `status` — low cardinality (4 and 3 distinct values respectively) makes B-tree indexes counterproductive; the query planner will prefer sequential scans. `domain` index deferred until query patterns justify it.

### JSONB schemas

**`models`:**
```json
{
  "fields": [
    {
      "name": "customer_id",
      "type": "string",
      "description": "Unique customer identifier",
      "nullable": false,
      "primary_key": true
    }
  ]
}
```

**`servicelevels`:**
```json
{
  "freshness": "24h",
  "availability": "99.9%",
  "retention": "365d",
  "latency": "1h"
}
```

---

## Backend

### Domain Entity

`DataContract` replaces `obj: dict` with typed fields:

```python
class DataContract:
    id: UUID
    title: str
    version: str        # semver string e.g. "1.0.0"
    owner: str
    domain: str
    tier: int           # 1–4
    status: str         # "draft" | "active" | "deprecated"
    models: dict        # ModelsSection payload
    servicelevels: dict # ServiceLevels payload
    created_at: datetime
    updated_at: datetime
```

### Pydantic Schemas

Three nested models:

```
SchemaField:        name, type, description, nullable (bool), primary_key (bool)
ModelsSection:      fields: list[SchemaField]
ServiceLevels:      freshness, availability, retention, latency (all str, optional)

DataContractCreateModel:
    title: str
    version: str = "1.0.0"
    owner: str
    domain: str
    tier: int  (Field ge=1, le=4)
    status: Literal["draft", "in_review", "active", "deprecated"] = "draft"
    models: ModelsSection = ModelsSection()
    servicelevels: ServiceLevels = ServiceLevels()

DataContractUpdateModel:  same fields, all optional
DataContractResponseModel: all fields + id, created_at, updated_at
```

### New Endpoint

`GET /data-contracts/{id}/yaml`

Assembles and returns an ODCS-compliant YAML string from the stored columns. No separate storage — built on the fly:

```yaml
dataContractSpecification: 0.9.3
id: <uuid>
info:
  title: ...
  version: ...
  owner: ...
  domain: ...
  status: ...
models:
  fields:
    - name: ...
      type: ...
servicelevels:
  freshness: ...
  availability: ...
  retention: ...
  latency: ...
x-tier: 2
```

Response: `text/plain` (or `application/yaml`). Frontend fetches it on demand.

### Repository & Use Cases

Existing `create`, `get`, `list`, `update`, `delete` use cases keep the same shape. Only the SQL queries and parameter mapping change — named columns instead of a single `obj` parameter. No new use cases.

---

## Frontend

### Contract Creation — Dedicated Page

Creation moves from a modal to a full page at `/data-contracts/new`. The "New Contract" button in the list page navigates there. The page has four sequential steps rendered as a single scrollable form (not tabs), with a step indicator at the top.

**Step 1 — Tier Wizard**

Four yes/no questions, each revealed after the previous answer:

1. "Could an error in this data cause a regulatory, legal, or financial consequence?" → yes = Tier 1
2. "Could an error lead to a wrong business decision with measurable financial impact?" → yes = Tier 2
3. "Is the impact of an error manageable informally, with no material damage?" → yes = Tier 3
4. (default) → Tier 4

After answering, the assigned tier is shown with its name and a short description. The user can override via a dropdown. The wizard result feeds the `tier` field in the form.

**Step 2 — Contract Info**

Named inputs: `title`, `version` (prefilled `1.0.0`), `owner`, `domain`, `status` (select: draft / in_review / active / deprecated).

**Step 3 — Models**

Dynamic field builder. Each row: `name` (text), `type` (select: string / integer / float / boolean / date / timestamp), `description` (text), `nullable` (toggle), `primary_key` (toggle). Add/remove rows with buttons. No JSON editing exposed.

**Step 4 — Service Levels**

Four optional text inputs: `freshness`, `availability`, `retention`, `latency`. Placeholder hints (e.g. `24h`, `99.9%`).

A "Create Contract" button at the bottom submits the assembled payload.

### Detail Page — Structured View

Replaces the raw JSON `<pre>` block with:

- **Info card** — tier badge (color-coded: 1=red, 2=orange, 3=blue, 4=gray), status badge (draft=gray, in_review=yellow, active=green, deprecated=red), owner, domain, version
- **Models table** — columns: field name, type, nullable, PK, description
- **Service Levels card** — four labeled values
- **"View YAML" button** — fetches `GET /data-contracts/{id}/yaml` and renders the result in a `<pre>` block inside a modal
- **Approval actions** — shown only when `status === 'in_review'`: an **Approve** button (sets status to `active`) and a **Request Changes** button (sets status back to `draft`). Both are plain `PATCH` calls — no RBAC enforcement in this iteration.

Edit flow: the existing edit modal gets the same structured form (pre-populated), replacing the JSON textarea.

### Type Changes

`DataContract` in `types/index.ts`:

```typescript
export interface DataContract {
  id: string
  title: string
  version: string
  owner: string
  domain: string
  tier: 1 | 2 | 3 | 4
  status: 'draft' | 'in_review' | 'active' | 'deprecated'
  models: { fields: SchemaField[] }
  servicelevels: { freshness: string; availability: string; retention: string; latency: string }
  created_at: string
  updated_at: string
}

export interface SchemaField {
  name: string
  type: 'string' | 'integer' | 'float' | 'boolean' | 'date' | 'timestamp'
  description: string
  nullable: boolean
  primary_key: boolean
}
```

The list page `Contract Preview` column changes to show `title` + tier badge instead of the first JSON key.

---

## Out of Scope (this iteration)

- Git PR creation on contract submit
- Approval workflows
- Consumer registration
- Input/output port declarations
- Continuous quality validation
- Full ODCS field coverage (`servers`, `terms`, `links`, `custom`)

Adding any of these later requires no DB migration — new ODCS sections extend `models`/`servicelevels` JSONB or add new JSONB columns without touching the flat metadata columns.
