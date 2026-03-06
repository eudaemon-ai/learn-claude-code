# s03: TodoWrite

`s01 > s02 > [ s03 ] s04 > s05 > s06 | s07 > s08 > s09 > s10 > s11 > s12`

> *"Ένας agent χωρίς σχέδιο παρασύρεται"* -- κατάγραψε πρώτα τα βήματα, μετά εκτέλεσε.

## Πρόβλημα

Σε εργασίες πολλαπλών βημάτων, το μοντέλο χάνει το νήμα. Επαναλαμβάνει δουλειά, παραλείπει βήματα, ή ξεφεύγει. Μακρές συνομιλίες το κάνουν χειρότερο -- το system prompt ξεθωριάζει καθώς τα αποτελέσματα εργαλείων γεμίζουν το context. Μια αναδιοργάνωση 10 βημάτων μπορεί να ολοκληρώσει τα βήματα 1-3, και μετά το μοντέλο αρχίζει να αυτοσχεδιάζει επειδή ξέχασε τα βήματα 4-10.

## Λύση

```
+--------+      +-------+      +---------+
|  User  | ---> |  LLM  | ---> | Tools   |
| prompt |      |       |      | + todo  |
+--------+      +---+---+      +----+----+
                    ^                |
                    |   tool_result  |
                    +----------------+
                          |
              +-----------+-----------+
              | TodoManager state     |
              | [ ] task A            |
              | [>] task B  <- doing  |
              | [x] task C            |
              +-----------------------+
                          |
              if rounds_since_todo >= 3:
                inject <reminder> into tool_result
```

## Πώς Λειτουργεί

1. Το TodoManager αποθηκεύει στοιχεία με καταστάσεις. Μόνο ένα στοιχείο μπορεί να είναι `in_progress` κάθε φορά.

```python
class TodoManager:
    def update(self, items: list) -> str:
        validated, in_progress_count = [], 0
        for item in items:
            status = item.get("status", "pending")
            if status == "in_progress":
                in_progress_count += 1
            validated.append({"id": item["id"], "text": item["text"],
                              "status": status})
        if in_progress_count > 1:
            raise ValueError("Only one task can be in_progress")
        self.items = validated
        return self.render()
```

2. Το εργαλείο `todo` μπαίνει στο dispatch map όπως κάθε άλλο εργαλείο.

```python
TOOL_HANDLERS = {
    # ...base tools...
    "todo": lambda **kw: TODO.update(kw["items"]),
}
```

3. Μια υπενθύμιση nag εισάγει ένα σκούντημα αν το μοντέλο περάσει 3+ γύρους χωρίς να καλέσει το `todo`.

```python
if rounds_since_todo >= 3 and messages:
    last = messages[-1]
    if last["role"] == "user" and isinstance(last.get("content"), list):
        last["content"].insert(0, {
            "type": "text",
            "text": "<reminder>Update your todos.</reminder>",
        })
```

Ο περιορισμός "ένα in_progress κάθε φορά" επιβάλλει διαδοχική εστίαση. Η υπενθύμιση nag δημιουργεί λογοδοσία.

## Τι Άλλαξε Από το s02

| Component      | Πριν (s02)       | Μετά (s03)                 |
|----------------|------------------|----------------------------|
| Tools          | 4                | 5 (+todo)                  |
| Planning       | Κανένα           | TodoManager με καταστάσεις |
| Nag injection  | Κανένα           | `<reminder>` μετά από 3 γύρους|
| Agent loop     | Απλό dispatch    | + rounds_since_todo counter|

## Δοκίμασέ το

```sh
cd learn-claude-code
python agents/s03_todo_write.py
```

1. `Refactor the file hello.py: add type hints, docstrings, and a main guard`
2. `Create a Python package with __init__.py, utils.py, and tests/test_utils.py`
3. `Review all Python files and fix any style issues`
