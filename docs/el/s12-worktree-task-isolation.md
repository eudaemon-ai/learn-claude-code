# s12: Worktree + Απομόνωση Εργασιών

`s01 > s02 > s03 > s04 > s05 > s06 | s07 > s08 > s09 > s10 > s11 > [ s12 ]`

> *"Ο καθένας δουλεύει στον δικό του κατάλογο, χωρίς παρεμβολή"* -- οι εργασίες διαχειρίζονται στόχους, τα worktrees διαχειρίζονται καταλόγους, δεμένα με ID.

## Πρόβλημα

Μέχρι το s11, οι agents μπορούν να διεκδικήσουν και να ολοκληρώσουν εργασίες αυτόνομα. Αλλά κάθε εργασία τρέχει σε έναν κοινό κατάλογο. Δύο agents που αναδιοργανώνουν διαφορετικά modules ταυτόχρονα θα συγκρουστούν: ο agent A επεξεργάζεται το `config.py`, ο agent B επεξεργάζεται το `config.py`, οι μη staged αλλαγές αναμειγνύονται, και κανένας δεν μπορεί να κάνει rollback καθαρά.

Ο πίνακας εργασιών παρακολουθεί *τι να κάνεις* αλλά δεν έχει γνώμη για το *πού να το κάνεις*. Η λύση: δώσε σε κάθε εργασία τον δικό της κατάλογο git worktree. Οι εργασίες διαχειρίζονται στόχους, τα worktrees διαχειρίζονται context εκτέλεσης. Δέσε τα με task ID.

## Λύση

```
Control plane (.tasks/)             Execution plane (.worktrees/)
+------------------+                +------------------------+
| task_1.json      |                | auth-refactor/         |
|   status: in_progress  <------>   branch: wt/auth-refactor
|   worktree: "auth-refactor"   |   task_id: 1             |
+------------------+                +------------------------+
| task_2.json      |                | ui-login/              |
|   status: pending    <------>     branch: wt/ui-login
|   worktree: "ui-login"       |   task_id: 2             |
+------------------+                +------------------------+
                                    |
                          index.json (worktree registry)
                          events.jsonl (lifecycle log)

State machines:
  Task:     pending -> in_progress -> completed
  Worktree: absent  -> active      -> removed | kept
```

## Πώς Λειτουργεί

1. **Δημιούργησε μια εργασία.** Διατήρησε πρώτα τον στόχο.

```python
TASKS.create("Implement auth refactor")
# -> .tasks/task_1.json  status=pending  worktree=""
```

2. **Δημιούργησε ένα worktree και δέσε το στην εργασία.** Περνώντας `task_id` προωθεί αυτόματα την εργασία σε `in_progress`.

```python
WORKTREES.create("auth-refactor", task_id=1)
# -> git worktree add -b wt/auth-refactor .worktrees/auth-refactor HEAD
# -> index.json gets new entry, task_1.json gets worktree="auth-refactor"
```

Η σύνδεση γράφει κατάσταση και στις δύο πλευρές:

```python
def bind_worktree(self, task_id, worktree):
    task = self._load(task_id)
    task["worktree"] = worktree
    if task["status"] == "pending":
        task["status"] = "in_progress"
    self._save(task)
```

3. **Τρέξε εντολές στο worktree.** Το `cwd` δείχνει στον απομονωμένο κατάλογο.

```python
subprocess.run(command, shell=True, cwd=worktree_path,
               capture_output=True, text=True, timeout=300)
```

4. **Κλείσιμο.** Δύο επιλογές:
   - `worktree_keep(name)` -- διατήρησε τον κατάλογο για αργότερα.
   - `worktree_remove(name, complete_task=True)` -- αφαίρεσε κατάλογο, ολοκλήρωσε τη δεμένη εργασία, εκπέμψε event. Μία κλήση χειρίζεται teardown + ολοκλήρωση.

```python
def remove(self, name, force=False, complete_task=False):
    self._run_git(["worktree", "remove", wt["path"]])
    if complete_task and wt.get("task_id") is not None:
        self.tasks.update(wt["task_id"], status="completed")
        self.tasks.unbind_worktree(wt["task_id"])
        self.events.emit("task.completed", ...)
```

5. **Ροή events.** Κάθε βήμα κύκλου ζωής εκπέμπει στο `.worktrees/events.jsonl`:

```json
{
  "event": "worktree.remove.after",
  "task": {"id": 1, "status": "completed"},
  "worktree": {"name": "auth-refactor", "status": "removed"},
  "ts": 1730000000
}
```

Events που εκπέμπονται: `worktree.create.before/after/failed`, `worktree.remove.before/after/failed`, `worktree.keep`, `task.completed`.

Μετά από crash, η κατάσταση ανακατασκευάζεται από `.tasks/` + `.worktrees/index.json` στο δίσκο. Η μνήμη συνομιλίας είναι πτητική· η κατάσταση αρχείων είναι ανθεκτική.

## Τι Άλλαξε Από το s11

| Component          | Πριν (s11)                 | Μετά (s12)                                   |
|--------------------|----------------------------|----------------------------------------------|
| Coordination       | Πίνακας εργασιών (owner/status)| Πίνακας εργασιών + ρητή σύνδεση worktree  |
| Execution scope    | Κοινός κατάλογος           | Απομονωμένος κατάλογος ανά εργασία           |
| Recoverability     | Μόνο κατάσταση εργασίας    | Κατάσταση εργασίας + ευρετήριο worktree      |
| Teardown           | Ολοκλήρωση εργασίας        | Ολοκλήρωση εργασίας + ρητό keep/remove       |
| Lifecycle visibility | Υπονοούμενο σε logs      | Ρητά events στο `.worktrees/events.jsonl`    |

## Δοκίμασέ το

```sh
cd learn-claude-code
python agents/s12_worktree_task_isolation.py
```

1. `Create tasks for backend auth and frontend login page, then list tasks.`
2. `Create worktree "auth-refactor" for task 1, then bind task 2 to a new worktree "ui-login".`
3. `Run "git status --short" in worktree "auth-refactor".`
4. `Keep worktree "ui-login", then list worktrees and inspect events.`
5. `Remove worktree "auth-refactor" with complete_task=true, then list tasks/worktrees/events.`
