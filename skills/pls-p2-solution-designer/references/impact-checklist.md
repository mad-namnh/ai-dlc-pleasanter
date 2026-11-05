# Impact checklist

For each change, walk every existing element of the affected sites (from `config/<site>/site.json` and scripts) and answer.

| If the change… | Check | Example |
|---|---|---|
| adds / removes / renames a **status** | views with `Status` filters; notifications watching `Status` or using a view as condition; aggregations by status; process `CurrentStatus`/`ChangedStatus`; scripts with status maps | an "open items" view filtering on the old statuses would hide records in the new status → derived requirement; a script mapping status codes to labels needs the new code |
| adds / removes a **choice** | records using the choice (removal = data-impacting, D11); filters and conditions listing choices | — |
| adds a **column** | slot free and never used with data; editor layout; grid; filters; exports; scripts that iterate columns | a stamp column set by a process is read-only and placed next to related fields |
| removes a **column** | data in the slot → data-impacting; formulas/links/lookups referencing it | — |
| adds a **process / button** | who may execute (access control); repeat execution; behaviour outside the condition (API enforces it, D10) | who may press it is an open question unless the requirement says so; repeat execution prevented by the display condition on status |
| changes **notifications** | recipients exist in every environment; mail testability | mail delivery is usually not testable on dev → carry as an open point |
| changes **permissions** | permission matrix before/after → permission-impacting | — |
| touches **scripts** | ladder reason; D3/D5/D7 rules; timeouts | — |
| touches **links / lookups / summaries** | cross-site references resolved per environment (`${site:…}`) | — |
