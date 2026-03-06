# s04: Subagents

`s01 > s02 > s03 > [ s04 ] s05 > s06 | s07 > s08 > s09 > s10 > s11 > s12`

> *"Σπάσε μεγάλες εργασίες· κάθε υποεργασία παίρνει καθαρό context"* -- οι subagents χρησιμοποιούν ανεξάρτητα messages[], κρατώντας την κύρια συνομιλία καθαρή.

## Πρόβλημα

Καθώς ο agent δουλεύει, ο πίνακας messages του μεγαλώνει. Κάθε ανάγνωση αρχείου, κάθε έξοδος bash μένει στο context μόνιμα. "Ποιο testing framework χρησιμοποιεί αυτό το project;" μπορεί να απαιτεί ανάγνωση 5 αρχείων, αλλά ο parent χρειάζεται μόνο την απάντηση: "pytest."

## Λύση

```
Parent agent                     Subagent
+------------------+             +------------------+
| messages=[...]   |             | messages=[]      | <-- fresh
|                  |  dispatch   |                  |
| tool: task       | ----------> | while tool_use:  |
|   prompt="..."   |             |   call tools     |
|                  |  summary    |   append results |
|   result = "..." | <---------- | return last text |
+------------------+             +------------------+

Parent context stays clean. Subagent context is discarded.
```

## Πώς Λειτουργεί

1. Ο parent παίρνει ένα εργαλείο `task`. Το child παίρνει όλα τα βασικά εργαλεία εκτός από το `task` (όχι αναδρομική δημιουργία).

```python
PARENT_TOOLS = CHILD_TOOLS + [
    {"name": "task",
     "description": "Spawn a subagent with fresh context.",
     "input_schema": {
         "type": "object",
         "properties": {"prompt": {"type": "string"}},
         "required": ["prompt"],
     }},
]
```

2. Ο subagent ξεκινά με `messages=[]` και τρέχει τον δικό του βρόχο. Μόνο το τελικό κείμενο επιστρέφει στον parent.

```python
def run_subagent(prompt: str) -> str:
    sub_messages = [{"role": "user", "content": prompt}]
    for _ in range(30):  # safety limit
        response = client.messages.create(
            model=MODEL, system=SUBAGENT_SYSTEM,
            messages=sub_messages,
            tools=CHILD_TOOLS, max_tokens=8000,
        )
        sub_messages.append({"role": "assistant",
                             "content": response.content})
        if response.stop_reason != "tool_use":
            break
        results = []
        for block in response.content:
            if block.type == "tool_use":
                handler = TOOL_HANDLERS.get(block.name)
                output = handler(**block.input)
                results.append({"type": "tool_result",
                    "tool_use_id": block.id,
                    "content": str(output)[:50000]})
        sub_messages.append({"role": "user", "content": results})
    return "".join(
        b.text for b in response.content if hasattr(b, "text")
    ) or "(no summary)"
```

Ολόκληρο το ιστορικό μηνυμάτων του child (πιθανώς 30+ κλήσεις εργαλείων) απορρίπτεται. Ο parent λαμβάνει μια περίληψη μιας παραγράφου ως κανονικό `tool_result`.

## Τι Άλλαξε Από το s03

| Component      | Πριν (s03)       | Μετά (s04)                |
|----------------|------------------|---------------------------|
| Tools          | 5                | 5 (base) + task (parent)  |
| Context        | Ενιαίο κοινό     | Parent + child isolation  |
| Subagent       | Κανένα           | `run_subagent()` function |
| Return value   | N/A              | Μόνο κείμενο περίληψης    |

## Δοκίμασέ το

```sh
cd learn-claude-code
python agents/s04_subagent.py
```

1. `Use a subtask to find what testing framework this project uses`
2. `Delegate: read all .py files and summarize what each one does`
3. `Use a task to create a new module, then verify it from here`
