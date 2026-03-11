[English](./README.md) | [中文](./README-zh.md) | [日本語](./README-ja.md) | [Ελληνικά](./README-el.md)
# Μάθε Claude Code -- Ένας νάνο Claude Code-like agent, χτισμένος από το 0 στο 1
<img width="260" src="https://github.com/user-attachments/assets/fe8b852b-97da-4061-a467-9694906b5edf" /><br>

Σκανάρετε με Wechat για να μας ακολουθήσετε,  
ή ακολουθήστε στο X: [EudaemonAI](https://x.com/baicai003)  


```
                    THE AGENT PATTERN
                    =================

    User --> messages[] --> LLM --> response
                                      |
                            stop_reason == "tool_use"?
                           /                          \
                         yes                           no
                          |                             |
                    execute tools                    return text
                    append results
                    loop back -----------------> messages[]


    That's the minimal loop. Every AI coding agent needs this loop.
    Production agents add policy, permissions, and lifecycle layers.
```

**12 προοδευτικές συνεδρίες, από έναν απλό βρόχο σε απομονωμένη αυτόνομη εκτέλεση.**
**Κάθε συνεδρία προσθέτει έναν μηχανισμό. Κάθε μηχανισμός έχει ένα μότο.**

> **s01** &nbsp; *"Ένας βρόχος & Bash είναι όλα όσα χρειάζεσαι"* &mdash; ένα εργαλείο + ένας βρόχος = ένας agent
>
> **s02** &nbsp; *"Προσθέτοντας ένα εργαλείο σημαίνει προσθήκη ενός handler"* &mdash; ο βρόχος παραμένει ίδιος· νέα εργαλεία καταχωρούνται στο dispatch map
>
> **s03** &nbsp; *"Ένας agent χωρίς σχέδιο παρασύρεται"* &mdash; κατάγραψε πρώτα τα βήματα, μετά εκτέλεσε· η ολοκλήρωση διπλασιάζεται
>
> **s04** &nbsp; *"Σπάσε μεγάλες εργασίες· κάθε υποεργασία παίρνει καθαρό context"* &mdash; οι subagents χρησιμοποιούν ανεξάρτητα messages[], κρατώντας την κύρια συνομιλία καθαρή
>
> **s05** &nbsp; *"Φόρτωσε γνώση όταν τη χρειάζεσαι, όχι εκ των προτέρων"* &mdash; εισάγεις μέσω tool_result, όχι στο system prompt
>
> **s06** &nbsp; *"Το context θα γεμίσει· χρειάζεσαι τρόπο να κάνεις χώρο"* &mdash; στρατηγική συμπίεσης τριών επιπέδων για άπειρες συνεδρίες
>
> **s07** &nbsp; *"Σπάσε μεγάλους στόχους σε μικρές εργασίες, τακτοποίησέ τες, αποθήκευσε στο δίσκο"* &mdash; ένα file-based task graph με εξαρτήσεις, θέτοντας τα θεμέλια για συνεργασία πολλαπλών agents
>
> **s08** &nbsp; *"Τρέξε αργές λειτουργίες στο παρασκήνιο· ο agent συνεχίζει να σκέφτεται"* &mdash; daemon threads τρέχουν εντολές, εισάγουν ειδοποιήσεις κατά την ολοκλήρωση
>
> **s09** &nbsp; *"Όταν η εργασία είναι πολύ μεγάλη για έναν, ανάθεσε σε συναδέλφους"* &mdash; persistent teammates + async mailboxes
>
> **s10** &nbsp; *"Οι συνάδελφοι χρειάζονται κοινούς κανόνες επικοινωνίας"* &mdash; ένα request-response pattern οδηγεί όλη τη διαπραγμάτευση
>
> **s11** &nbsp; *"Οι συνάδελφοι σαρώνουν τον πίνακα και διεκδικούν εργασίες μόνοι τους"* &mdash; δεν χρειάζεται ο επικεφαλής να αναθέτει κάθε μία
>
> **s12** &nbsp; *"Ο καθένας δουλεύει στο δικό του directory, χωρίς παρεμβολές"* &mdash; τα tasks διαχειρίζονται στόχους, τα worktrees διαχειρίζονται directories, δεμένα με ID

---

## Το Βασικό Pattern

```python
def agent_loop(messages):
    while True:
        response = client.messages.create(
            model=MODEL, system=SYSTEM,
            messages=messages, tools=TOOLS,
        )
        messages.append({"role": "assistant",
                         "content": response.content})

        if response.stop_reason != "tool_use":
            return

        results = []
        for block in response.content:
            if block.type == "tool_use":
                output = TOOL_HANDLERS[block.name](**block.input)
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": output,
                })
        messages.append({"role": "user", "content": results})
```

Κάθε συνεδρία στρώνει έναν μηχανισμό πάνω σε αυτόν τον βρόχο -- χωρίς να αλλάζει τον ίδιο τον βρόχο.

## Πεδίο Εφαρμογής (Σημαντικό)

Αυτό το repository είναι ένα 0->1 εκπαιδευτικό project για την κατασκευή ενός νάνο Claude Code-like agent.
Απλοποιεί ή παραλείπει σκόπιμα αρκετούς production μηχανισμούς:

- Πλήρεις event/hook buses (για παράδειγμα PreToolUse, SessionStart/End, ConfigChange).  
  Το s12 περιλαμβάνει μόνο ένα ελάχιστο append-only lifecycle event stream για διδακτικούς σκοπούς.
- Rule-based permission governance και trust workflows
- Session lifecycle controls (resume/fork) και προηγμένα worktree lifecycle controls
- Πλήρεις λεπτομέρειες MCP runtime (transport/OAuth/resource subscribe/polling)

Αντιμετωπίστε το team JSONL mailbox protocol σε αυτό το repo ως διδακτική υλοποίηση, όχι ως ισχυρισμό για συγκεκριμένα production internals.

## Γρήγορη Εκκίνηση

```sh
git clone https://github.com/eudaemon-ai/learn-claude-code
cd learn-claude-code
pip install -r requirements.txt
cp .env.example .env   # Edit .env with your ANTHROPIC_API_KEY

python agents/s01_agent_loop.py       # Start here
python agents/s12_worktree_task_isolation.py  # Full progression endpoint
python agents/s_full.py               # Capstone: all mechanisms combined
```

### Web Platform

Διαδραστικές οπτικοποιήσεις, διαγράμματα βήμα-βήμα, source viewer, και τεκμηρίωση.

```sh
cd web && npm install && npm run dev   # http://localhost:3000
```

## Μαθησιακή Διαδρομή

```
Phase 1: THE LOOP                    Phase 2: PLANNING & KNOWLEDGE
==================                   ==============================
s01  The Agent Loop          [1]     s03  TodoWrite               [5]
     while + stop_reason                  TodoManager + nag reminder
     |                                    |
     +-> s02  Tool Use            [4]     s04  Subagents            [5]
              dispatch map: name->handler     fresh messages[] per child
                                              |
                                         s05  Skills               [5]
                                              SKILL.md via tool_result
                                              |
                                         s06  Context Compact      [5]
                                              3-layer compression

Phase 3: PERSISTENCE                 Phase 4: TEAMS
==================                   =====================
s07  Tasks                   [8]     s09  Agent Teams             [9]
     file-based CRUD + deps graph         teammates + JSONL mailboxes
     |                                    |
s08  Background Tasks        [6]     s10  Team Protocols          [12]
     daemon threads + notify queue        shutdown + plan approval FSM
                                          |
                                     s11  Autonomous Agents       [14]
                                          idle cycle + auto-claim
                                     |
                                     s12  Worktree Isolation      [16]
                                          task coordination + optional isolated execution lanes

                                     [N] = number of tools
```

## Αρχιτεκτονική

```
learn-claude-code/
|
|-- agents/                        # Python reference implementations (s01-s12 + s_full capstone)
|-- docs/{en,zh,ja,el}/            # Mental-model-first documentation (4 languages)
|-- web/                           # Interactive learning platform (Next.js)
|-- skills/                        # Skill files for s05
+-- .github/workflows/ci.yml      # CI: typecheck + build
```

## Τεκμηρίωση

Mental-model-first: πρόβλημα, λύση, ASCII διάγραμμα, ελάχιστος κώδικας.
Διαθέσιμη σε [English](./docs/en/) | [中文](./docs/zh/) | [日本語](./docs/ja/) | [Ελληνικά](./docs/el/).

| Συνεδρία | Θέμα | Μότο |
|---------|-------|-------|
| [s01](./docs/el/s01-the-agent-loop.md) | Ο Βρόχος του Agent | *Ένας βρόχος & Bash είναι όλα όσα χρειάζεσαι* |
| [s02](./docs/el/s02-tool-use.md) | Χρήση Εργαλείων | *Προσθέτοντας ένα εργαλείο σημαίνει προσθήκη ενός handler* |
| [s03](./docs/el/s03-todo-write.md) | TodoWrite | *Ένας agent χωρίς σχέδιο παρασύρεται* |
| [s04](./docs/el/s04-subagent.md) | Subagents | *Σπάσε μεγάλες εργασίες· κάθε υποεργασία παίρνει καθαρό context* |
| [s05](./docs/el/s05-skill-loading.md) | Skills | *Φόρτωσε γνώση όταν τη χρειάζεσαι, όχι εκ των προτέρων* |
| [s06](./docs/el/s06-context-compact.md) | Context Compact | *Το context θα γεμίσει· χρειάζεσαι τρόπο να κάνεις χώρο* |
| [s07](./docs/el/s07-task-system.md) | Tasks | *Σπάσε μεγάλους στόχους σε μικρές εργασίες, τακτοποίησέ τες, αποθήκευσε στο δίσκο* |
| [s08](./docs/el/s08-background-tasks.md) | Background Tasks | *Τρέξε αργές λειτουργίες στο παρασκήνιο· ο agent συνεχίζει να σκέφτεται* |
| [s09](./docs/el/s09-agent-teams.md) | Agent Teams | *Όταν η εργασία είναι πολύ μεγάλη για έναν, ανάθεσε σε συναδέλφους* |
| [s10](./docs/el/s10-team-protocols.md) | Team Protocols | *Οι συνάδελφοι χρειάζονται κοινούς κανόνες επικοινωνίας* |
| [s11](./docs/el/s11-autonomous-agents.md) | Autonomous Agents | *Οι συνάδελφοι σαρώνουν τον πίνακα και διεκδικούν εργασίες μόνοι τους* |
| [s12](./docs/el/s12-worktree-task-isolation.md) | Worktree + Task Isolation | *Ο καθένας δουλεύει στο δικό του directory, χωρίς παρεμβολές* |

## Τι Ακολουθεί -- από την κατανόηση στην παράδοση

Μετά τις 12 συνεδρίες καταλαβαίνεις πώς λειτουργεί ένας agent από μέσα προς τα έξω. Δύο τρόποι να βάλεις αυτή τη γνώση σε δουλειά:

### Kode Agent CLI -- Open-Source Coding Agent CLI

> `npm i -g @eudaemon-ai/kode`

Υποστήριξη Skill & LSP, έτοιμο για Windows, pluggable με GLM / MiniMax / DeepSeek και άλλα ανοιχτά μοντέλα. Εγκατάστησε και ξεκίνα.

GitHub: **[eudaemon-ai/Kode-cli](https://github.com/eudaemon-ai/Kode-cli)**

### Kode Agent SDK -- Ενσωμάτωσε Agent Capabilities στην Εφαρμογή σου

Το επίσημο Claude Code Agent SDK επικοινωνεί με μια πλήρη CLI διαδικασία στο παρασκήνιο -- κάθε ταυτόχρονος χρήστης σημαίνει μια ξεχωριστή terminal διαδικασία. Το Kode SDK είναι μια αυτόνομη βιβλιοθήκη χωρίς overhead διαδικασίας ανά χρήστη, ενσωματώσιμη σε backends, browser extensions, embedded devices, ή οποιοδήποτε runtime.

GitHub: **[eudaemon-ai/Kode-agent-sdk](https://github.com/eudaemon-ai/Kode-agent-sdk)**

---

## Αδελφό Repo: από *on-demand sessions* σε *always-on assistant*

Ο agent που διδάσκει αυτό το repo είναι **use-and-discard** -- άνοιξε ένα terminal, δώσε του μια εργασία, κλείσε όταν τελειώσεις, η επόμενη συνεδρία ξεκινά κενή. Αυτό είναι το μοντέλο Claude Code.

Το [OpenClaw](https://github.com/openclaw/openclaw) απέδειξε μια άλλη δυνατότητα: πάνω στον ίδιο agent πυρήνα, δύο μηχανισμοί μετατρέπουν τον agent από "σπρώξε τον για να κινηθεί" σε "ξυπνάει κάθε 30 δευτερόλεπτα για να ψάξει για δουλειά":

- **Heartbeat** -- κάθε 30s το σύστημα στέλνει στον agent ένα μήνυμα να ελέγξει αν υπάρχει κάτι να κάνει. Τίποτα; Πήγαινε πίσω για ύπνο. Κάτι; Ενέργησε αμέσως.
- **Cron** -- ο agent μπορεί να προγραμματίσει τις δικές του μελλοντικές εργασίες, που εκτελούνται αυτόματα όταν έρθει η ώρα.

Πρόσθεσε multi-channel IM routing (WhatsApp / Telegram / Slack / Discord, 13+ πλατφόρμες), persistent context memory, και ένα Soul personality system, και ο agent πηγαίνει από ένα disposable εργαλείο σε έναν always-on προσωπικό AI βοηθό.

Το **[claw0](https://github.com/eudaemon-ai/claw0)** είναι το συνοδευτικό μας διδακτικό repo που αποδομεί αυτούς τους μηχανισμούς από το μηδέν:

```
claw agent = agent core + heartbeat + cron + IM chat + memory + soul
```

```
learn-claude-code                   claw0
(agent runtime core:                (proactive always-on assistant:
 loop, tools, planning,              heartbeat, cron, IM channels,
 teams, worktree isolation)          memory, soul personality)
```

## Άδεια

MIT

---

**Το μοντέλο είναι ο agent. Η δουλειά μας είναι να του δώσουμε εργαλεία και να μείνουμε έξω από το δρόμο.**
