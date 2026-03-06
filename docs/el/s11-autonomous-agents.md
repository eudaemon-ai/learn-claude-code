# s11: Αυτόνομοι Agents

`s01 > s02 > s03 > s04 > s05 > s06 | s07 > s08 > s09 > s10 > [ s11 ] s12`

> *"Οι συμπαίκτες σαρώνουν τον πίνακα και διεκδικούν εργασίες μόνοι τους"* -- δεν χρειάζεται ο lead να αναθέτει κάθε μία.

## Πρόβλημα

Στο s09-s10, οι συμπαίκτες δουλεύουν μόνο όταν τους λένε ρητά. Ο lead πρέπει να δημιουργήσει τον καθένα με ένα συγκεκριμένο prompt. 10 αδιεκδίκητες εργασίες στον πίνακα; Ο lead αναθέτει κάθε μία χειροκίνητα. Δεν κλιμακώνεται.

Αληθινή αυτονομία: οι συμπαίκτες σαρώνουν τον πίνακα εργασιών μόνοι τους, διεκδικούν αδιεκδίκητες εργασίες, δουλεύουν πάνω τους, μετά ψάχνουν για περισσότερες.

Μια λεπτότητα: μετά από συμπίεση context (s06), ο agent μπορεί να ξεχάσει ποιος είναι. Η επανεισαγωγή ταυτότητας το διορθώνει αυτό.

## Λύση

```
Teammate lifecycle with idle cycle:

+-------+
| spawn |
+---+---+
    |
    v
+-------+   tool_use     +-------+
| WORK  | <------------- |  LLM  |
+---+---+                +-------+
    |
    | stop_reason != tool_use (or idle tool called)
    v
+--------+
|  IDLE  |  poll every 5s for up to 60s
+---+----+
    |
    +---> check inbox --> message? ----------> WORK
    |
    +---> scan .tasks/ --> unclaimed? -------> claim -> WORK
    |
    +---> 60s timeout ----------------------> SHUTDOWN

Identity re-injection after compression:
  if len(messages) <= 3:
    messages.insert(0, identity_block)
```

## Πώς Λειτουργεί

1. Ο βρόχος teammate έχει δύο φάσεις: WORK και IDLE. Όταν το LLM σταματά να καλεί εργαλεία (ή καλεί το `idle`), ο teammate μπαίνει σε IDLE.

```python
def _loop(self, name, role, prompt):
    while True:
        # -- WORK PHASE --
        messages = [{"role": "user", "content": prompt}]
        for _ in range(50):
            response = client.messages.create(...)
            if response.stop_reason != "tool_use":
                break
            # execute tools...
            if idle_requested:
                break

        # -- IDLE PHASE --
        self._set_status(name, "idle")
        resume = self._idle_poll(name, messages)
        if not resume:
            self._set_status(name, "shutdown")
            return
        self._set_status(name, "working")
```

2. Η φάση idle κάνει poll το inbox και τον πίνακα εργασιών σε βρόχο.

```python
def _idle_poll(self, name, messages):
    for _ in range(IDLE_TIMEOUT // POLL_INTERVAL):  # 60s / 5s = 12
        time.sleep(POLL_INTERVAL)
        inbox = BUS.read_inbox(name)
        if inbox:
            messages.append({"role": "user",
                "content": f"<inbox>{inbox}</inbox>"})
            return True
        unclaimed = scan_unclaimed_tasks()
        if unclaimed:
            claim_task(unclaimed[0]["id"], name)
            messages.append({"role": "user",
                "content": f"<auto-claimed>Task #{unclaimed[0]['id']}: "
                           f"{unclaimed[0]['subject']}</auto-claimed>"})
            return True
    return False  # timeout -> shutdown
```

3. Σάρωση πίνακα εργασιών: βρες pending, χωρίς ιδιοκτήτη, μη μπλοκαρισμένες εργασίες.

```python
def scan_unclaimed_tasks() -> list:
    unclaimed = []
    for f in sorted(TASKS_DIR.glob("task_*.json")):
        task = json.loads(f.read_text())
        if (task.get("status") == "pending"
                and not task.get("owner")
                and not task.get("blockedBy")):
            unclaimed.append(task)
    return unclaimed
```

4. Επανεισαγωγή ταυτότητας: όταν το context είναι πολύ σύντομο (έγινε συμπίεση), εισήγαγε ένα μπλοκ ταυτότητας.

```python
if len(messages) <= 3:
    messages.insert(0, {"role": "user",
        "content": f"<identity>You are '{name}', role: {role}, "
                   f"team: {team_name}. Continue your work.</identity>"})
    messages.insert(1, {"role": "assistant",
        "content": f"I am {name}. Continuing."})
```

## Τι Άλλαξε Από το s10

| Component      | Πριν (s10)       | Μετά (s11)                 |
|----------------|------------------|----------------------------|
| Tools          | 12               | 14 (+idle, +claim_task)    |
| Autonomy       | Καθοδηγούμενο από lead| Αυτο-οργανωμένο         |
| Idle phase     | Κανένα           | Poll inbox + task board    |
| Task claiming  | Μόνο χειροκίνητα | Αυτόματη διεκδίκηση αδιεκδίκητων εργασιών|
| Identity       | System prompt    | + επανεισαγωγή μετά από compress|
| Timeout        | Κανένα           | 60s idle -> auto shutdown  |

## Δοκίμασέ το

```sh
cd learn-claude-code
python agents/s11_autonomous_agents.py
```

1. `Create 3 tasks on the board, then spawn alice and bob. Watch them auto-claim.`
2. `Spawn a coder teammate and let it find work from the task board itself`
3. `Create tasks with dependencies. Watch teammates respect the blocked order.`
4. Type `/tasks` to see the task board with owners
5. Type `/team` to monitor who is working vs idle
