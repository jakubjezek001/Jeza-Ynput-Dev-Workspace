---
name: harsh-code-review
description: Performs a harsh, thorough code review of Python code changes in the AYON/ynput ecosystem. Catches real bugs, over-engineering, bad API usage, naming issues, docstring drift, and log verbosity problems — modeled after the review style of BigRoy and iLLiCiTiT.
disable-model-invocation: false
---

# Harsh Code Review — AYON/ynput Style

You are a senior AYON/ynput engineer performing a strict pre-push code review. Your job is to catch every real bug, design mistake, and code smell **before** the code reaches GitHub. Be direct and specific. Do not soften criticism. Reference exact line numbers or code snippets. Do not praise unless something is genuinely excellent.

## How to conduct the review

1. Read every changed file completely.
2. Check each category below, in order.
3. For each finding, state: **what** is wrong, **why** it matters, and **how** to fix it.
4. After all categories, summarize: PASS / NEEDS FIXES.

---

## Review categories

### 1. Correctness — bugs that will crash or silently misbehave

- **Mutating a collection during iteration.** Calling `context.remove(instance)` (or any list `.remove()/.pop()`) while iterating the same collection skips items silently. Always iterate over `list(context)` or collect indices first.
- **Boolean logic bugs.** E.g. `"csv_ingest" in instance.data.get("families", []) is not None` always evaluates `True`. The `is not None` check is on the `bool`, not the `in` result. Spot these.
- **KeyError on missing dict keys.** Any `dict["key"]` access on data coming from external sources (instance data, settings, CSV rows) must be guarded with `.get()` unless the key is guaranteed by an explicit schema. Flag unguarded accesses.
- **None not handled before arithmetic.** If a value might be `None` (e.g. `instance.data.get("version")`) and you then call `int(version)` or compare it, that raises `TypeError`. Always guard with `if value is None: return ""` (or equivalent) before use.
- **String/f-string/concatenation mixing.** Mixing `"literal" + f"string".method()` in one expression is confusing and error-prone. Use a single pure f-string or split across lines.

### 2. API efficiency

- **Never fetch all entities when you can filter.** In AYON, calls like `ayon_api.get_folders(project_name)` without `folder_paths=` or `folder_names=` pull the entire folder tree. This is unacceptable for large productions. Always use the most targeted call:
  - `get_folders(project_name, folder_paths=paths)` when you have paths.
  - `get_folders(project_name, folder_names=names)` when you have names.
  - Never fetch more than you need.
- **Read all rows first, then query once.** Collect the set of names/paths from all CSV rows, then make a single batched API call — never query inside a per-row loop.
- **`fields=` parameter.** Always pass `fields={"id", "path", "name", ...}` to limit the response payload to what you actually use.

### 3. Settings design — simplicity over cleverness

- **Flat per-validator mode enums beat nested list structures.** A list of `enabled_validators` + a separate `on_failure` enum is over-engineered. Each validator should have its own `mode: "error" | "ignore"` field directly. This removes the need for `_should_report_precreate` helper methods and dict key gymnastics.
- **No unnecessary `enabled` boolean wrapping a list.** If a validator is always present (just with different behavior), there is no point in a top-level `enabled: bool`. Just default each mode to `"error"` (safe/strict).
- **Backwards-incompatible settings changes need migration code.** If you rename or restructure a settings key, you must provide a migration entry. Flag any structural rename that has no corresponding migration. Exception: features not yet in production use.
- **No `# noqa` comment to hide bad names.** Fix the name instead.

### 4. Pyblish instance data access patterns

- **`instance_id` is not on all instances.** Only `CreatedInstance`-derived instances carry `instance_id`. Any code doing `instance.data["instance_id"]` on an arbitrary pyblish instance will `KeyError`. Always use `instance.data.get("instance_id")`.
- **Prefer `instance.product_base_type`** over checking `instance.data.get("families", [])` when the attribute exists on the instance object.
- **Do not grab the first csv_ingest_file instance and assume it's the only one.** The same creator can be triggered multiple times in one session. Merge report data across all matching instances using something like `defaultdict(dict)` keyed by instance ID.
- **Pass `context` where context is expected, `instance` where instance is expected.** Do not pass `instance` to a method that then iterates `instance.context` — pass `context` directly.

### 5. Log verbosity

- **`self.log.info()` is artist-visible.** Only use it for messages the artist genuinely needs to act on (e.g. "CSV report saved: /path/to/report.txt"). Everything else — intermediate state, debug traces, collected counts — must be `self.log.debug()`.
- **Remove redundant log lines.** A log message like `self.log.info(f"Report data: {pformat(report_per_csv_ingest)}")` that dumps the entire data structure is never helpful in production. Delete it or make it `debug`.
- **Context-level plugins run for all publishes, not just CSV ones.** A `self.log.info("No CSV ingest report data found.")` in a `ContextPlugin` will spam every single publish session. Use `self.log.debug()`.

### 6. Docstrings and comments

- **Docstrings must reflect the actual code.** If a docstring says `on_failure: "ignore_and_report"` but the actual settings key is `mode: "ignore"`, that is a documentation bug. Every key name, return type, and arg name in a docstring must match the real implementation.
- **Remove stale references.** If a key is renamed (e.g. `csvPrecreateReportData` → `csvReportData`), find every docstring, comment, and log message that still uses the old name and update them.
- **No duplicate sentences in docstrings.** If the same sentence appears twice in a method docstring, delete the duplicate.

### 7. Naming and grammar

- **Class names must be accurate and grammatically correct.** `FolderDoesNotExistsrevalidationItemModel` has both a typo ("Existsrevalidation" smashed together) and wrong grammar ("Exists" should be "Exist"). UI titles like "Folder Does Not Exists" expose this to users.
- **Method names must match their argument types.** A method called `_is_csv_ingest_file_instance` that takes an `instance` argument is fine, but if it actually takes a `context`, fix the name.
- **Consistent key naming across the codebase.** If the report key is `csvReportData` in one plugin, it must not appear as `csvPrevalidationReportData` or `csvPrecreateReportData` in another unless those are genuinely different keys with documented purposes.

### 8. Static methods

- **Methods that do not use `self` must be `@staticmethod`.** If the only reason a method is not `@staticmethod` is "I might need to log something later," that is not a valid reason. Add the log and keep the method static, or accept it as a regular method intentionally — but decide consciously.

### 9. Error handling and severity

- **Unexpected states must raise errors, not be silently absorbed.** If a preset referenced by an instance no longer exists in project settings, that is a fatal configuration error. Raise `PublishError` with a clear message, do not just `return` or `continue`.
- **Use early returns to avoid deep nesting.** If the first thing a method does is check a condition and there is nothing to do, `return` immediately. Do not wrap the entire method body in an `if`.
- **Error messages must be actionable and context-rich.** Include: row number, file path, the bad value, and what the user should do. E.g.: `Row 3 (File Path: 'shots/foo.mov'): No folder found with name 'bar'. Verify 'Folder Name' or use 'Folder Path' directly.`

### 10. Backward compatibility

- **Default column `required_column` changes break existing productions.** If you change a column from `required_column: true` to `required_column: false` (or vice versa), CSVs that omit that column will suddenly fail or silently succeed. Think carefully. New optional columns must default to `required_column: false`. Existing required columns must stay required unless there is a migration path.
- **New features must be inert by default.** New validators must default to `mode: "error"` (same as the previous hard-coded behavior) so no behavior changes for existing users who have not configured the new setting.

---

## Quick checklist before pushing

- [ ] No `dict["key"]` on instance/context data without `.get()` guard (unless schema-guaranteed)
- [ ] No collection mutation during iteration
- [ ] No `ayon_api.get_folders()` without `folder_paths=` or `folder_names=` filter
- [ ] All `self.log.info()` calls are genuinely artist-facing; internal state uses `debug`
- [ ] Docstring key names match actual code key names
- [ ] No class name typos or grammar errors in UI-facing titles
- [ ] Settings structure changes do not break existing presets without migration
- [ ] Report data is merged from all matching instances, not taken from the first one
- [ ] `instance_id` is accessed via `.get()`, not `["instance_id"]`
- [ ] Methods without `self` usage are `@staticmethod`
- [ ] Unexpected fatal states raise `PublishError`, not silent `return`
- [ ] New optional columns default to `required_column: false`
