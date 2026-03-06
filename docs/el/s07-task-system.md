# s07: Σύστημα Εργασιών

`s01 > s02 > s03 > s04 > s05 > s06 | [ s07 ] s08 > s09 > s10 > s11 > s12`

> *"Σπάσε μεγάλους στόχους σε μικρές εργασίες, τακτοποίησέ τες, διατήρησέ τες στο δίσκο"* -- ένα σύστημα γράφου εργασιών βασισμένο σε αρχεία με εξαρτήσεις, θέτοντας τα θεμέλια για συνεργασία πολλαπλών agents.

## Πρόβλημα

Το TodoManager του s03 είναι μια επίπεδη λίστα ελέγχου στη μνήμη: χωρίς σειρά, χωρίς εξαρτήσεις, χωρίς κατάσταση πέρα από ολοκληρωμένο-ή-όχι. Οι πραγματικοί στόχοι έχουν δομή -- η εργασία B εξαρτάται από την εργασία A, οι εργασίες C και D μπορούν να τρέξουν παράλληλα, η εργασία E περιμένει και τις C και D.

Χωρίς ρητές σχέσεις, ο agent δεν μπορεί να πει τι είναι έτοιμο, τι είναι μπλοκαρισμένο, ή τι μπορεί να τρέξει ταυτόχρονα. Και επειδή η λίστα ζει μόνο στη μνήμη, η συμπίεση context (s06) τη σβήνει καθαρά.

## Λύση

Προάγαγε τη λίστα ελέγχου σε **γράφο εργασιών** που διατηρείται στο δίσκο. Κάθε εργασία είναι ένα αρχείο JSON με κατάσταση, εξαρτήσεις (`blockedBy`), και εξαρτώμενα (`blocks`). Ο γράφος απαντά σε τρεις ερωτήσεις κάθε στιγμή:

- **Τι είναι έτοιμο;** -- εργασίες με κατάσταση `pending` και κενό `blockedBy`.
- **Τι είναι μπλοκαρισμένο;** -- εργασίες που περιμένουν ημιτελείς εξαρτήσεις.
- **Τι είναι ολοκληρωμένο;** -- εργασίες `completed`, των οποίων η ολοκλήρωση ξεμπλοκάρει αυτόματα τα εξαρτώμενα.

```
.tasks/
  task_1.json  {"id":1, "status":"completed"}
  task_2.json  {"id":2, "blockedBy":[1], "status":"pending"}
  task_3.json  {"id":3, "blockedBy":[1], "status":"pending"}
  task_4.json  {"id":4, "blockedBy":[2,3], "status":"pending"}

Task graph (DAG):
                 +----------+
            +--> | task 2   | --+
            |    | pending  |   |
+----------+     +----------+    +--> +----------+
| task 1   |                          | task 4   |
| completed| --> +----------+    +--> | blocked  |
+----------+     | task 3   | --+     +----------+
                 | pending  |
                 +----------+

Ordering:     task 1 must finish before 2 and 3
Parallelism:  tasks 2 and 3 can run at the same time
Dependencies: task 4 waits for both 2 and 3
Status:       pending -> in_progress -> completed
```

Αυτός ο γράφος εργασιών γίνεται η ραχοκοκαλιά συντονισμού για όλα μετά το s07: εκτέλεση παρασκηνίου (s08), ομάδες πολλαπλών agents (s09+), και απομόνωση worktree (s12) όλα διαβάζουν από και γράφουν σε αυτή την ίδια δομή.

## Πώς Λειτουργεί

1. **TaskManager**: ένα αρχείο JSON ανά εργασία, CRUD με γράφο εξαρτήσεων.

```python
class TaskManager:
    def __init__(self, tasks_dir: Path):
        self.dir = tasks_dir
        self.dir.mkdir(exist_ok=True)
        self._next_id = self._max_id() + 1

    def create(self, subject, description=""):
        task = {"id": self._next_id, "subject": subject,
                "status": "pending", "blockedBy": [],
                "blocks": [], "owner": ""}
        self._save(task)
        self._next_id += 1
        return json.dumps(task, indent=2)
```

2. **Επίλυση εξαρτήσεων**: η ολοκλήρωση μιας εργασίας καθαρίζει το ID της από τη λίστα `blockedBy` κάθε άλλης εργασίας, ξεμπλοκάροντας αυτόματα τα εξαρτώμενα.

```python
def _clear_dependency(self, completed_id):
    for f in self.dir.glob("task_*.json"):
        task = json.loads(f.read_text())
        if completed_id in task.get("blockedBy", []):
            task["blockedBy"].remove(completed_id)
            self._save(task)
```

3. **Κατάσταση + καλωδίωση εξαρτήσεων**: το `update` χειρίζεται μεταβάσεις και άκρες εξαρτήσεων.

```python
def update(self, task_id, status=None,
           add_blocked_by=None, add_blocks=None):
    task = self._load(task_id)
    if status:
        task["status"] = status
        if status == "completed":
            self._clear_dependency(task_id)
    self._save(task)
```

4. Τέσσερα εργαλεία εργασιών μπαίνουν στο dispatch map.

```python
TOOL_HANDLERS = {
    # ...base tools...
    "task_create": lambda **kw: TASKS.create(kw["subject"]),
    "task_update": lambda **kw: TASKS.update(kw["task_id"], kw.get("status")),
    "task_list":   lambda **kw: TASKS.list_all(),
    "task_get":    lambda **kw: TASKS.get(kw["task_id"]),
}
```

Από το s07 και μετά, ο γράφος εργασιών είναι η προεπιλογή για δουλειά πολλαπλών βημάτων. Το Todo του s03 παραμένει για γρήγορες λίστες ελέγχου μιας συνεδρίας.

## Τι Άλλαξε Από το s06

| Component | Πριν (s06) | Μετά (s07) |
|---|---|---|
| Tools | 5 | 8 (`task_create/update/list/get`) |
| Planning model | Επίπεδη λίστα ελέγχου (στη μνήμη) | Γράφος εργασιών με εξαρτήσεις (στο δίσκο) |
| Relationships | Κανένα | Άκρες `blockedBy` + `blocks` |
| Status tracking | Ολοκληρωμένο ή όχι | `pending` -> `in_progress` -> `completed` |
| Persistence | Χάνεται στη συμπίεση | Επιβιώνει συμπίεσης και επανεκκινήσεων |

## Δοκίμασέ το

```sh
cd learn-claude-code
python agents/s07_task_system.py
```

1. `Create 3 tasks: "Setup project", "Write code", "Write tests". Make them depend on each other in order.`
2. `List all tasks and show the dependency graph`
3. `Complete task 1 and then list tasks to see task 2 unblocked`
4. `Create a task board for refactoring: parse -> transform -> emit -> test, where transform and emit can run in parallel after parse`
