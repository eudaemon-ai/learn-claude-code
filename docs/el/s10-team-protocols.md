# s10: Πρωτόκολλα Ομάδας

`s01 > s02 > s03 > s04 > s05 > s06 | s07 > s08 > s09 > [ s10 ] s11 > s12`

> *"Οι συμπαίκτες χρειάζονται κοινούς κανόνες επικοινωνίας"* -- ένα μοτίβο αίτησης-απάντησης οδηγεί όλη τη διαπραγμάτευση.

## Πρόβλημα

Στο s09, οι συμπαίκτες δουλεύουν και επικοινωνούν αλλά στερούνται δομημένου συντονισμού:

**Shutdown**: Το σκότωμα ενός thread αφήνει αρχεία μισογραμμένα και το config.json ξεπερασμένο. Χρειάζεσαι μια χειραψία: ο lead ζητά, ο teammate εγκρίνει (τελείωσε και έξοδος) ή απορρίπτει (συνέχισε να δουλεύεις).

**Έγκριση σχεδίου**: Όταν ο lead λέει "αναδιοργάνωσε το auth module," ο teammate ξεκινά αμέσως. Για αλλαγές υψηλού κινδύνου, ο lead πρέπει να αναθεωρήσει πρώτα το σχέδιο.

Και τα δύο μοιράζονται την ίδια δομή: η μία πλευρά στέλνει μια αίτηση με ένα μοναδικό ID, η άλλη απαντά αναφέροντας αυτό το ID.

## Λύση

```
Shutdown Protocol            Plan Approval Protocol
==================           ======================

Lead             Teammate    Teammate           Lead
  |                 |           |                 |
  |--shutdown_req-->|           |--plan_req------>|
  | {req_id:"abc"}  |           | {req_id:"xyz"}  |
  |                 |           |                 |
  |<--shutdown_resp-|           |<--plan_resp-----|
  | {req_id:"abc",  |           | {req_id:"xyz",  |
  |  approve:true}  |           |  approve:true}  |

Shared FSM:
  [pending] --approve--> [approved]
  [pending] --reject---> [rejected]

Trackers:
  shutdown_requests = {req_id: {target, status}}
  plan_requests     = {req_id: {from, plan, status}}
```

## Πώς Λειτουργεί

1. Ο lead ξεκινά shutdown δημιουργώντας ένα request_id και στέλνοντας μέσω του inbox.

```python
shutdown_requests = {}

def handle_shutdown_request(teammate: str) -> str:
    req_id = str(uuid.uuid4())[:8]
    shutdown_requests[req_id] = {"target": teammate, "status": "pending"}
    BUS.send("lead", teammate, "Please shut down gracefully.",
             "shutdown_request", {"request_id": req_id})
    return f"Shutdown request {req_id} sent (status: pending)"
```

2. Ο teammate λαμβάνει την αίτηση και απαντά με approve/reject.

```python
if tool_name == "shutdown_response":
    req_id = args["request_id"]
    approve = args["approve"]
    shutdown_requests[req_id]["status"] = "approved" if approve else "rejected"
    BUS.send(sender, "lead", args.get("reason", ""),
             "shutdown_response",
             {"request_id": req_id, "approve": approve})
```

3. Η έγκριση σχεδίου ακολουθεί το ίδιο ακριβώς μοτίβο. Ο teammate υποβάλλει ένα σχέδιο (δημιουργώντας ένα request_id), ο lead αναθεωρεί (αναφέροντας το ίδιο request_id).

```python
plan_requests = {}

def handle_plan_review(request_id, approve, feedback=""):
    req = plan_requests[request_id]
    req["status"] = "approved" if approve else "rejected"
    BUS.send("lead", req["from"], feedback,
             "plan_approval_response",
             {"request_id": request_id, "approve": approve})
```

Ένα FSM, δύο εφαρμογές. Η ίδια μηχανή κατάστασης `pending -> approved | rejected` χειρίζεται οποιοδήποτε πρωτόκολλο αίτησης-απάντησης.

## Τι Άλλαξε Από το s09

| Component      | Πριν (s09)       | Μετά (s10)                   |
|----------------|------------------|------------------------------|
| Tools          | 9                | 12 (+shutdown_req/resp +plan)|
| Shutdown       | Μόνο φυσική έξοδος| Χειραψία αίτησης-απάντησης  |
| Plan gating    | Κανένα           | Υποβολή/αναθεώρηση με έγκριση|
| Correlation    | Κανένα           | request_id ανά αίτηση        |
| FSM            | Κανένα           | pending -> approved/rejected |

## Δοκίμασέ το

```sh
cd learn-claude-code
python agents/s10_team_protocols.py
```

1. `Spawn alice as a coder. Then request her shutdown.`
2. `List teammates to see alice's status after shutdown approval`
3. `Spawn bob with a risky refactoring task. Review and reject his plan.`
4. `Spawn charlie, have him submit a plan, then approve it.`
5. Type `/team` to monitor statuses
