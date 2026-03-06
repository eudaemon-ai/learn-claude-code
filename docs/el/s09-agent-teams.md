# s09: Ομάδες Agents

`s01 > s02 > s03 > s04 > s05 > s06 | s07 > s08 > [ s09 ] s10 > s11 > s12`

> *"Όταν η εργασία είναι πολύ μεγάλη για έναν, ανάθεσε σε συμπαίκτες"* -- μόνιμοι συμπαίκτες + ασύγχρονα mailboxes.

## Πρόβλημα

Οι subagents (s04) είναι μιας χρήσης: δημιούργησε, δούλεψε, επέστρεψε περίληψη, πέθανε. Χωρίς ταυτότητα, χωρίς μνήμη μεταξύ κλήσεων. Οι εργασίες παρασκηνίου (s08) τρέχουν εντολές shell αλλά δεν μπορούν να πάρουν αποφάσεις καθοδηγούμενες από LLM.

Η πραγματική ομαδική εργασία χρειάζεται: (1) μόνιμους agents που επιβιώνουν ενός μόνο prompt, (2) διαχείριση ταυτότητας και κύκλου ζωής, (3) ένα κανάλι επικοινωνίας μεταξύ agents.

## Λύση

```
Teammate lifecycle:
  spawn -> WORKING -> IDLE -> WORKING -> ... -> SHUTDOWN

Communication:
  .team/
    config.json           <- team roster + statuses
    inbox/
      alice.jsonl         <- append-only, drain-on-read
      bob.jsonl
      lead.jsonl

              +--------+    send("alice","bob","...")    +--------+
              | alice  | -----------------------------> |  bob   |
              | loop   |    bob.jsonl << {json_line}    |  loop  |
              +--------+                                +--------+
                   ^                                         |
                   |        BUS.read_inbox("alice")          |
                   +---- alice.jsonl -> read + drain ---------+
```

## Πώς Λειτουργεί

1. Το TeammateManager διατηρεί το config.json με τη λίστα της ομάδας.

```python
class TeammateManager:
    def __init__(self, team_dir: Path):
        self.dir = team_dir
        self.dir.mkdir(exist_ok=True)
        self.config_path = self.dir / "config.json"
        self.config = self._load_config()
        self.threads = {}
```

2. Το `spawn()` δημιουργεί έναν teammate και ξεκινά τον βρόχο agent του σε ένα thread.

```python
def spawn(self, name: str, role: str, prompt: str) -> str:
    member = {"name": name, "role": role, "status": "working"}
    self.config["members"].append(member)
    self._save_config()
    thread = threading.Thread(
        target=self._teammate_loop,
        args=(name, role, prompt), daemon=True)
    thread.start()
    return f"Spawned teammate '{name}' (role: {role})"
```

3. MessageBus: append-only JSONL inboxes. Το `send()` προσθέτει μια γραμμή JSON· το `read_inbox()` διαβάζει όλα και αδειάζει.

```python
class MessageBus:
    def send(self, sender, to, content, msg_type="message", extra=None):
        msg = {"type": msg_type, "from": sender,
               "content": content, "timestamp": time.time()}
        if extra:
            msg.update(extra)
        with open(self.dir / f"{to}.jsonl", "a") as f:
            f.write(json.dumps(msg) + "\n")

    def read_inbox(self, name):
        path = self.dir / f"{name}.jsonl"
        if not path.exists(): return "[]"
        msgs = [json.loads(l) for l in path.read_text().strip().splitlines() if l]
        path.write_text("")  # drain
        return json.dumps(msgs, indent=2)
```

4. Κάθε teammate ελέγχει το inbox του πριν από κάθε κλήση LLM, εισάγοντας ληφθέντα μηνύματα στο context.

```python
def _teammate_loop(self, name, role, prompt):
    messages = [{"role": "user", "content": prompt}]
    for _ in range(50):
        inbox = BUS.read_inbox(name)
        if inbox != "[]":
            messages.append({"role": "user",
                "content": f"<inbox>{inbox}</inbox>"})
            messages.append({"role": "assistant",
                "content": "Noted inbox messages."})
        response = client.messages.create(...)
        if response.stop_reason != "tool_use":
            break
        # execute tools, append results...
    self._find_member(name)["status"] = "idle"
```

## Τι Άλλαξε Από το s08

| Component      | Πριν (s08)       | Μετά (s09)                 |
|----------------|------------------|----------------------------|
| Tools          | 6                | 9 (+spawn/send/read_inbox) |
| Agents         | Μονός            | Lead + N teammates         |
| Persistence    | Κανένα           | config.json + JSONL inboxes|
| Threads        | Background cmds  | Πλήροι βρόχοι agent ανά thread|
| Lifecycle      | Fire-and-forget  | idle -> working -> idle    |
| Communication  | Κανένα           | message + broadcast        |

## Δοκίμασέ το

```sh
cd learn-claude-code
python agents/s09_agent_teams.py
```

1. `Spawn alice (coder) and bob (tester). Have alice send bob a message.`
2. `Broadcast "status update: phase 1 complete" to all teammates`
3. `Check the lead inbox for any messages`
4. Type `/team` to see the team roster with statuses
5. Type `/inbox` to manually check the lead's inbox
