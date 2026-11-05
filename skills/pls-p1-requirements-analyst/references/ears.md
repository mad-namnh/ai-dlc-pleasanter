# EARS patterns (Easy Approach to Requirements Syntax)

| Type | Pattern | Pleasanter example |
|---|---|---|
| Ubiquitous | The `<system>` shall `<response>`. | The 貸出中 view shall list loans in status 貸出中 and 督促済. |
| Event-driven | When `<trigger>`, the `<system>` shall `<response>`. | When 総務 executes 督促, the system shall set the status to 督促済 and record the reminder date-time. |
| State-driven | While `<state>`, the `<system>` shall `<response>`. | While a loan is past its 返却期限 and not returned, the system shall offer the 督促 action. |
| Unwanted behaviour | If `<condition>`, then the `<system>` shall `<response>`. | If a loan has been returned, then the system shall not offer the 督促 action. |
| Optional feature | Where `<feature is included>`, the `<system>` shall `<response>`. | Where mail notification is enabled, the system shall notify the borrower. |
| Complex | Combinations of the above. | While …, when …, the system shall … |

## Rules

- Use Pleasanter UI terms exactly as the users see them (Japanese labels). Do not put column slot names (ClassE, DateC) in the statement; mention them only in notes for P2.
- "The system" is the Pleasanter site, not a person.
- No design words in the requirement (no "process", "server script", "ClassC") unless the customer used them; keep design for P2.
- One `shall` per requirement. Split otherwise.
