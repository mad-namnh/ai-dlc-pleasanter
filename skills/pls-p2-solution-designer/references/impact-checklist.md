# Impact checklist — how to walk the impact rules

The rules themselves are in `impact-rules.md` (generated from `pls classify` and the KB — never edit it by hand; a
rule that is missing there is a framework change, not a project note).

1. List what the change does, per affected site: statuses, choices, columns, links / lookups / summaries, formulas,
   processes, status controls, permissions and access lists, notifications and reminders, scripts, other settings.
2. For each item, find every rule in `impact-rules.md` whose "If the change…" matches. Include rules of class
   *design*: no tool decides them.
3. For each matching rule, walk every existing element of the affected sites (`config/<site>/site.json`, scripts,
   `pls xref --site <s>`) and answer what the rule's "The design checks and states" column asks, using the KB advice
   it cites.
4. Write one row per matching rule in the DES impact table, with its rule id. A rule that matches but changes nothing
   still gets a row ("checked: none").
5. New impacts become derived requirements → back to P1 / G1; do not absorb them silently.
6. Run `pls scope --site <s>` for every site whose settings the design changes (rule SE-SCOPE): each key it lists needs
   a probe before G2 or a decision record, named in the DES front matter `unverified` (`key`, and `probe` or
   `decision`); G3 compares them with the built site.
