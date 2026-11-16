# Review — site lists mapped

## Round 1 (pls-x-reviewer, opus, high) — accept with fixes; no Critical/High

- **M1:** QuickAccessSites JSON shapes not mapped / not reported (number Id, `id` key, trailing comma, single quotes) → number Id and any-case `Id` mapped; text starting with "[" that Python cannot read is reported by lint and refused by pack (other lists of the part still mapped); tests. Whether Pleasanter's Deserialize accepts lenient JSON: not verified (Implem.Libraries not in the clone).
- **M2:** remedy "use its SiteName" relies on names pls neither deploys nor checks → messages now say write `${site:<name>}`; the limit is in the module docstring.
- **M3:** MoveTargets missing from the sandbox shared-write check → added to `_writes_to`; test.
- **L1:** ASCII digits only (full-width digits are names); IntegratedSites name-first limit documented. **L2:** a name is rewritten only when it maps (no trimming). **L3:** lint reports any MoveTargets element that is not `${site:x}`. **L4:** lint names the key and dashboard part. **L5:** inventory summary updated; adopt `referenced_sites` does not list these lists — disposition: lint reports them right after adopt (L-PERM-01). **L6:** plan labels removed from the module docstring.
