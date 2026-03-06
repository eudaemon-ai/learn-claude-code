# s06: Context Compact

`s01 > s02 > s03 > s04 > s05 > [ s06 ] | s07 > s08 > s09 > s10 > s11 > s12`

> *"Το context θα γεμίσει· χρειάζεσαι τρόπο να κάνεις χώρο"* -- στρατηγική συμπίεσης τριών επιπέδων για άπειρες συνεδρίες.

## Πρόβλημα

Το παράθυρο context είναι πεπερασμένο. Ένα μόνο `read_file` σε ένα αρχείο 1000 γραμμών κοστίζει ~4000 tokens. Μετά από ανάγνωση 30 αρχείων και εκτέλεση 20 εντολών bash, φτάνεις στα 100,000+ tokens. Ο agent δεν μπορεί να δουλέψει σε μεγάλες codebases χωρίς συμπίεση.

## Λύση

Τρία επίπεδα, αυξανόμενα σε επιθετικότητα:

```
Every turn:
+------------------+
| Tool call result |
+------------------+
        |
        v
[Layer 1: micro_compact]        (silent, every turn)
  Replace tool_result > 3 turns old
  with "[Previous: used {tool_name}]"
        |
        v
[Check: tokens > 50000?]
   |               |
   no              yes
   |               |
   v               v
continue    [Layer 2: auto_compact]
              Save transcript to .transcripts/
              LLM summarizes conversation.
              Replace all messages with [summary].
                    |
                    v
            [Layer 3: compact tool]
              Model calls compact explicitly.
              Same summarization as auto_compact.
```

## Πώς Λειτουργεί

1. **Layer 1 -- micro_compact**: Πριν από κάθε κλήση LLM, αντικατέστησε παλιά αποτελέσματα εργαλείων με placeholders.

```python
def micro_compact(messages: list) -> list:
    tool_results = []
    for i, msg in enumerate(messages):
        if msg["role"] == "user" and isinstance(msg.get("content"), list):
            for j, part in enumerate(msg["content"]):
                if isinstance(part, dict) and part.get("type") == "tool_result":
                    tool_results.append((i, j, part))
    if len(tool_results) <= KEEP_RECENT:
        return messages
    for _, _, part in tool_results[:-KEEP_RECENT]:
        if len(part.get("content", "")) > 100:
            part["content"] = f"[Previous: used {tool_name}]"
    return messages
```

2. **Layer 2 -- auto_compact**: Όταν τα tokens υπερβαίνουν το όριο, αποθήκευσε πλήρες transcript στο δίσκο, μετά ζήτησε από το LLM να συνοψίσει.

```python
def auto_compact(messages: list) -> list:
    # Save transcript for recovery
    transcript_path = TRANSCRIPT_DIR / f"transcript_{int(time.time())}.jsonl"
    with open(transcript_path, "w") as f:
        for msg in messages:
            f.write(json.dumps(msg, default=str) + "\n")
    # LLM summarizes
    response = client.messages.create(
        model=MODEL,
        messages=[{"role": "user", "content":
            "Summarize this conversation for continuity..."
            + json.dumps(messages, default=str)[:80000]}],
        max_tokens=2000,
    )
    return [
        {"role": "user", "content": f"[Compressed]\n\n{response.content[0].text}"},
        {"role": "assistant", "content": "Understood. Continuing."},
    ]
```

3. **Layer 3 -- manual compact**: Το εργαλείο `compact` ενεργοποιεί την ίδια σύνοψη κατά παραγγελία.

4. Ο βρόχος ενσωματώνει και τα τρία:

```python
def agent_loop(messages: list):
    while True:
        micro_compact(messages)                        # Layer 1
        if estimate_tokens(messages) > THRESHOLD:
            messages[:] = auto_compact(messages)       # Layer 2
        response = client.messages.create(...)
        # ... tool execution ...
        if manual_compact:
            messages[:] = auto_compact(messages)       # Layer 3
```

Τα transcripts διατηρούν πλήρες ιστορικό στο δίσκο. Τίποτα δεν χάνεται πραγματικά -- απλά μετακινείται εκτός ενεργού context.

## Τι Άλλαξε Από το s05

| Component      | Πριν (s05)       | Μετά (s06)                 |
|----------------|------------------|----------------------------|
| Tools          | 5                | 5 (base + compact)         |
| Context mgmt   | Κανένα           | Συμπίεση τριών επιπέδων    |
| Micro-compact  | Κανένα           | Παλιά αποτελέσματα -> placeholders|
| Auto-compact   | Κανένα           | Trigger ορίου tokens       |
| Transcripts    | Κανένα           | Αποθηκευμένα στο .transcripts/|

## Δοκίμασέ το

```sh
cd learn-claude-code
python agents/s06_context_compact.py
```

1. `Read every Python file in the agents/ directory one by one` (watch micro-compact replace old results)
2. `Keep reading files until compression triggers automatically`
3. `Use the compact tool to manually compress the conversation`
