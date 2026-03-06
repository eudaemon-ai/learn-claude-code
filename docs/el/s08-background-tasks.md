# s08: Εργασίες Παρασκηνίου

`s01 > s02 > s03 > s04 > s05 > s06 | s07 > [ s08 ] s09 > s10 > s11 > s12`

> *"Τρέξε αργές λειτουργίες στο παρασκήνιο· ο agent συνεχίζει να σκέφτεται"* -- daemon threads τρέχουν εντολές, εισάγουν ειδοποιήσεις κατά την ολοκλήρωση.

## Πρόβλημα

Μερικές εντολές παίρνουν λεπτά: `npm install`, `pytest`, `docker build`. Με έναν βρόχο που μπλοκάρει, το μοντέλο κάθεται αδρανές περιμένοντας. Αν ο χρήστης ρωτήσει "εγκατέστησε εξαρτήσεις και ενώ αυτό τρέχει, δημιούργησε το αρχείο config," ο agent τα κάνει διαδοχικά, όχι παράλληλα.

## Λύση

```
Main thread                Background thread
+-----------------+        +-----------------+
| agent loop      |        | subprocess runs |
| ...             |        | ...             |
| [LLM call] <---+------- | enqueue(result) |
|  ^drain queue   |        +-----------------+

Timeline:
Agent --[spawn A]--[spawn B]--[other work]----
             |          |
             v          v
          [A runs]   [B runs]      (parallel)
             |          |
             +-- results injected before next LLM call --+
```

## Πώς Λειτουργεί

1. Το BackgroundManager παρακολουθεί εργασίες με μια ουρά ειδοποιήσεων thread-safe.

```python
class BackgroundManager:
    def __init__(self):
        self.tasks = {}
        self._notification_queue = []
        self._lock = threading.Lock()
```

2. Το `run()` ξεκινά ένα daemon thread και επιστρέφει αμέσως.

```python
def run(self, command: str) -> str:
    task_id = str(uuid.uuid4())[:8]
    self.tasks[task_id] = {"status": "running", "command": command}
    thread = threading.Thread(
        target=self._execute, args=(task_id, command), daemon=True)
    thread.start()
    return f"Background task {task_id} started"
```

3. Όταν το subprocess τελειώνει, το αποτέλεσμά του πηγαίνει στην ουρά ειδοποιήσεων.

```python
def _execute(self, task_id, command):
    try:
        r = subprocess.run(command, shell=True, cwd=WORKDIR,
            capture_output=True, text=True, timeout=300)
        output = (r.stdout + r.stderr).strip()[:50000]
    except subprocess.TimeoutExpired:
        output = "Error: Timeout (300s)"
    with self._lock:
        self._notification_queue.append({
            "task_id": task_id, "result": output[:500]})
```

4. Ο βρόχος agent αδειάζει τις ειδοποιήσεις πριν από κάθε κλήση LLM.

```python
def agent_loop(messages: list):
    while True:
        notifs = BG.drain_notifications()
        if notifs:
            notif_text = "\n".join(
                f"[bg:{n['task_id']}] {n['result']}" for n in notifs)
            messages.append({"role": "user",
                "content": f"<background-results>\n{notif_text}\n"
                           f"</background-results>"})
            messages.append({"role": "assistant",
                "content": "Noted background results."})
        response = client.messages.create(...)
```

Ο βρόχος παραμένει single-threaded. Μόνο το subprocess I/O είναι παραλληλοποιημένο.

## Τι Άλλαξε Από το s07

| Component      | Πριν (s07)       | Μετά (s08)                 |
|----------------|------------------|----------------------------|
| Tools          | 8                | 6 (base + background_run + check)|
| Execution      | Μόνο blocking    | Blocking + background threads|
| Notification   | Κανένα           | Ουρά που αδειάζει ανά βρόχο|
| Concurrency    | Κανένα           | Daemon threads             |

## Δοκίμασέ το

```sh
cd learn-claude-code
python agents/s08_background_tasks.py
```

1. `Run "sleep 5 && echo done" in the background, then create a file while it runs`
2. `Start 3 background tasks: "sleep 2", "sleep 4", "sleep 6". Check their status.`
3. `Run pytest in the background and keep working on other things`
