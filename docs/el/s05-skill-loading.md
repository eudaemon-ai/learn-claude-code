# s05: Skills

`s01 > s02 > s03 > s04 > [ s05 ] s06 | s07 > s08 > s09 > s10 > s11 > s12`

> *"Φόρτωσε γνώση όταν τη χρειάζεσαι, όχι εκ των προτέρων"* -- εισαγωγή μέσω tool_result, όχι στο system prompt.

## Πρόβλημα

Θέλεις ο agent να ακολουθεί ροές εργασίας συγκεκριμένου τομέα: συμβάσεις git, μοτίβα testing, checklists αναθεώρησης κώδικα. Βάζοντας τα πάντα στο system prompt σπαταλάς tokens σε αχρησιμοποίητες δεξιότητες. 10 skills στα 2000 tokens το καθένα = 20,000 tokens, τα περισσότερα από τα οποία είναι άσχετα με οποιαδήποτε δεδομένη εργασία.

## Λύση

```
System prompt (Layer 1 -- always present):
+--------------------------------------+
| You are a coding agent.              |
| Skills available:                    |
|   - git: Git workflow helpers        |  ~100 tokens/skill
|   - test: Testing best practices     |
+--------------------------------------+

When model calls load_skill("git"):
+--------------------------------------+
| tool_result (Layer 2 -- on demand):  |
| <skill name="git">                   |
|   Full git workflow instructions...  |  ~2000 tokens
|   Step 1: ...                        |
| </skill>                             |
+--------------------------------------+
```

Layer 1: *ονόματα* skills στο system prompt (φθηνό). Layer 2: πλήρες *σώμα* μέσω tool_result (κατά παραγγελία).

## Πώς Λειτουργεί

1. Κάθε skill είναι ένας κατάλογος που περιέχει ένα `SKILL.md` με YAML frontmatter.

```
skills/
  pdf/
    SKILL.md       # ---\n name: pdf\n description: Process PDF files\n ---\n ...
  code-review/
    SKILL.md       # ---\n name: code-review\n description: Review code\n ---\n ...
```

2. Το SkillLoader σαρώνει για αρχεία `SKILL.md`, χρησιμοποιεί το όνομα του καταλόγου ως αναγνωριστικό skill.

```python
class SkillLoader:
    def __init__(self, skills_dir: Path):
        self.skills = {}
        for f in sorted(skills_dir.rglob("SKILL.md")):
            text = f.read_text()
            meta, body = self._parse_frontmatter(text)
            name = meta.get("name", f.parent.name)
            self.skills[name] = {"meta": meta, "body": body}

    def get_descriptions(self) -> str:
        lines = []
        for name, skill in self.skills.items():
            desc = skill["meta"].get("description", "")
            lines.append(f"  - {name}: {desc}")
        return "\n".join(lines)

    def get_content(self, name: str) -> str:
        skill = self.skills.get(name)
        if not skill:
            return f"Error: Unknown skill '{name}'."
        return f"<skill name=\"{name}\">\n{skill['body']}\n</skill>"
```

3. Το Layer 1 πηγαίνει στο system prompt. Το Layer 2 είναι απλά ένας άλλος handler εργαλείου.

```python
SYSTEM = f"""You are a coding agent at {WORKDIR}.
Skills available:
{SKILL_LOADER.get_descriptions()}"""

TOOL_HANDLERS = {
    # ...base tools...
    "load_skill": lambda **kw: SKILL_LOADER.get_content(kw["name"]),
}
```

Το μοντέλο μαθαίνει ποια skills υπάρχουν (φθηνό) και τα φορτώνει όταν είναι σχετικά (ακριβό).

## Τι Άλλαξε Από το s04

| Component      | Πριν (s04)       | Μετά (s05)                 |
|----------------|------------------|----------------------------|
| Tools          | 5 (base + task)  | 5 (base + load_skill)      |
| System prompt  | Στατικό string   | + περιγραφές skills        |
| Knowledge      | Κανένα           | skills/\*/SKILL.md files   |
| Injection      | Κανένα           | Δύο επίπεδα (system + result)|

## Δοκίμασέ το

```sh
cd learn-claude-code
python agents/s05_skill_loading.py
```

1. `What skills are available?`
2. `Load the agent-builder skill and follow its instructions`
3. `I need to do a code review -- load the relevant skill first`
4. `Build an MCP server using the mcp-builder skill`
