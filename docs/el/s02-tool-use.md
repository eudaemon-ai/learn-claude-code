# s02: Χρήση Εργαλείων

`s01 > [ s02 ] s03 > s04 > s05 > s06 | s07 > s08 > s09 > s10 > s11 > s12`

> *"Προσθέτοντας ένα εργαλείο σημαίνει προσθήκη ενός handler"* -- ο βρόχος παραμένει ίδιος· νέα εργαλεία καταχωρούνται στο dispatch map.

## Πρόβλημα

Με μόνο το `bash`, ο agent εκτελεί τα πάντα μέσω shell. Το `cat` περικόπτει απρόβλεπτα, το `sed` αποτυγχάνει σε ειδικούς χαρακτήρες, και κάθε κλήση bash είναι μια ανεξέλεγκτη επιφάνεια ασφαλείας. Αφιερωμένα εργαλεία όπως το `read_file` και το `write_file` σου επιτρέπουν να επιβάλεις sandboxing διαδρομών στο επίπεδο του εργαλείου.

Η βασική διορατικότητα: η προσθήκη εργαλείων δεν απαιτεί αλλαγή του βρόχου.

## Λύση

```
+--------+      +-------+      +------------------+
|  User  | ---> |  LLM  | ---> | Tool Dispatch    |
| prompt |      |       |      | {                |
+--------+      +---+---+      |   bash: run_bash |
                    ^           |   read: run_read |
                    |           |   write: run_wr  |
                    +-----------+   edit: run_edit |
                    tool_result | }                |
                                +------------------+

The dispatch map is a dict: {tool_name: handler_function}.
One lookup replaces any if/elif chain.
```

## Πώς Λειτουργεί

1. Κάθε εργαλείο παίρνει μια συνάρτηση handler. Το sandboxing διαδρομών αποτρέπει την απόδραση από το workspace.

```python
def safe_path(p: str) -> Path:
    path = (WORKDIR / p).resolve()
    if not path.is_relative_to(WORKDIR):
        raise ValueError(f"Path escapes workspace: {p}")
    return path

def run_read(path: str, limit: int = None) -> str:
    text = safe_path(path).read_text()
    lines = text.splitlines()
    if limit and limit < len(lines):
        lines = lines[:limit]
    return "\n".join(lines)[:50000]
```

2. Το dispatch map συνδέει ονόματα εργαλείων με handlers.

```python
TOOL_HANDLERS = {
    "bash":       lambda **kw: run_bash(kw["command"]),
    "read_file":  lambda **kw: run_read(kw["path"], kw.get("limit")),
    "write_file": lambda **kw: run_write(kw["path"], kw["content"]),
    "edit_file":  lambda **kw: run_edit(kw["path"], kw["old_text"],
                                        kw["new_text"]),
}
```

3. Στον βρόχο, αναζήτησε τον handler με το όνομα. Το σώμα του βρόχου παραμένει αμετάβλητο από το s01.

```python
for block in response.content:
    if block.type == "tool_use":
        handler = TOOL_HANDLERS.get(block.name)
        output = handler(**block.input) if handler \
            else f"Unknown tool: {block.name}"
        results.append({
            "type": "tool_result",
            "tool_use_id": block.id,
            "content": output,
        })
```

Πρόσθεσε ένα εργαλείο = πρόσθεσε έναν handler + πρόσθεσε μια καταχώρηση schema. Ο βρόχος δεν αλλάζει ποτέ.

## Τι Άλλαξε Από το s01

| Component      | Πριν (s01)         | Μετά (s02)                 |
|----------------|--------------------|----------------------------|
| Tools          | 1 (μόνο bash)      | 4 (bash, read, write, edit)|
| Dispatch       | Hardcoded bash call | `TOOL_HANDLERS` dict       |
| Path safety    | Κανένα             | `safe_path()` sandbox      |
| Agent loop     | Αμετάβλητο         | Αμετάβλητο                 |

## Δοκίμασέ το

```sh
cd learn-claude-code
python agents/s02_tool_use.py
```

1. `Read the file requirements.txt`
2. `Create a file called greet.py with a greet(name) function`
3. `Edit greet.py to add a docstring to the function`
4. `Read greet.py to verify the edit worked`
