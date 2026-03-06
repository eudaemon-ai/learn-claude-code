# s01: Ο Βρόχος του Agent

`[ s01 ] s02 > s03 > s04 > s05 > s06 | s07 > s08 > s09 > s10 > s11 > s12`

> *"Ένας βρόχος & Bash είναι όλα όσα χρειάζεσαι"* -- ένα εργαλείο + ένας βρόχος = ένας agent.

## Πρόβλημα

Ένα γλωσσικό μοντέλο μπορεί να συλλογιστεί για κώδικα, αλλά δεν μπορεί να *αγγίξει* τον πραγματικό κόσμο -- δεν μπορεί να διαβάσει αρχεία, να εκτελέσει tests, ή να ελέγξει σφάλματα. Χωρίς βρόχο, κάθε κλήση εργαλείου απαιτεί να αντιγράψεις-επικολλήσεις χειροκίνητα τα αποτελέσματα πίσω. Εσύ γίνεσαι ο βρόχος.

## Λύση

```
+--------+      +-------+      +---------+
|  User  | ---> |  LLM  | ---> |  Tool   |
| prompt |      |       |      | execute |
+--------+      +---+---+      +----+----+
                    ^                |
                    |   tool_result  |
                    +----------------+
                    (loop until stop_reason != "tool_use")
```

Μία συνθήκη εξόδου ελέγχει ολόκληρη τη ροή. Ο βρόχος τρέχει μέχρι το μοντέλο να σταματήσει να καλεί εργαλεία.

## Πώς Λειτουργεί

1. Το user prompt γίνεται το πρώτο μήνυμα.

```python
messages.append({"role": "user", "content": query})
```

2. Στείλε messages + tool definitions στο LLM.

```python
response = client.messages.create(
    model=MODEL, system=SYSTEM, messages=messages,
    tools=TOOLS, max_tokens=8000,
)
```

3. Πρόσθεσε την απάντηση του assistant. Έλεγξε το `stop_reason` -- αν το μοντέλο δεν κάλεσε εργαλείο, τελειώσαμε.

```python
messages.append({"role": "assistant", "content": response.content})
if response.stop_reason != "tool_use":
    return
```

4. Εκτέλεσε κάθε κλήση εργαλείου, συγκέντρωσε αποτελέσματα, πρόσθεσε ως user message. Επέστρεψε στο βήμα 2.

```python
results = []
for block in response.content:
    if block.type == "tool_use":
        output = run_bash(block.input["command"])
        results.append({
            "type": "tool_result",
            "tool_use_id": block.id,
            "content": output,
        })
messages.append({"role": "user", "content": results})
```

Συναρμολογημένο σε μία συνάρτηση:

```python
def agent_loop(query):
    messages = [{"role": "user", "content": query}]
    while True:
        response = client.messages.create(
            model=MODEL, system=SYSTEM, messages=messages,
            tools=TOOLS, max_tokens=8000,
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            return

        results = []
        for block in response.content:
            if block.type == "tool_use":
                output = run_bash(block.input["command"])
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": output,
                })
        messages.append({"role": "user", "content": results})
```

Αυτός είναι ολόκληρος ο agent σε λιγότερο από 30 γραμμές. Όλα τα υπόλοιπα σε αυτό το μάθημα στρώνονται από πάνω -- χωρίς να αλλάζουν τον βρόχο.

## Τι Άλλαξε

| Component     | Πριν       | Μετά                           |
|---------------|------------|--------------------------------|
| Agent loop    | (κανένα)   | `while True` + stop_reason     |
| Tools         | (κανένα)   | `bash` (ένα εργαλείο)          |
| Messages      | (κανένα)   | Συσσωρευτική λίστα             |
| Control flow  | (κανένα)   | `stop_reason != "tool_use"`    |

## Δοκίμασέ το

```sh
cd learn-claude-code
python agents/s01_agent_loop.py
```

1. `Create a file called hello.py that prints "Hello, World!"`
2. `List all Python files in this directory`
3. `What is the current git branch?`
4. `Create a directory called test_output and write 3 files in it`
