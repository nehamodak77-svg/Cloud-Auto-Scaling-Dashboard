# Cloud Auto-Scaling Dashboard

A **Flask API + React dashboard** built on top of the Colab notebook (VM manager + monitoring + auto-scaler).

```
autoscale-dashboard/
├── backend/                 # Flask (Python)
│   ├── app.py               # API routes - connects the three modules
│   ├── vm_manager.py        # Member 1: VM create/start/stop/delete (saved in vms.json)
│   ├── monitor.py           # Member 2: workload simulation + CPU/memory readings
│   ├── autoscaler.py        # Member 3: scale up / scale down decision logic
│   └── requirements.txt
└── frontend/                # React + Vite (plain CSS, no UI library)
    └── src/
        ├── App.jsx          # main page, calls /api/tick every 2 seconds
        ├── api.js           # all fetch() calls
        ├── styles.css
        └── components/      # StatCards, WorkloadControl, LineChart, VmTable,
                             # SettingsPanel, DecisionLog
```

## How to run (you need 2 terminals)

**Terminal 1: Backend**
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows   (Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt
python app.py                  # http://127.0.0.1:5001
```

**Terminal 2: Frontend**
```bash
cd frontend
npm install
npm run dev                    # http://localhost:5173  <- open this in the browser
```

## What the dashboard shows

- **Stat cards**: running VMs, average CPU / memory, simulated users
- **Workload simulator**: Low (10) / Medium (100) / High (500) users
- **Auto-scaler ON/OFF** switch and editable settings (thresholds, min/max VMs, cooldown)
- **Live charts**: CPU & memory (with threshold lines) and running VMs
- **VM table**: create, start, stop, edit config, delete
- **Decision log**: when and why the auto-scaler scaled

## How to demo it

1. Keep the auto-scaler ON and set the workload to **High**. CPU goes to ~100% and a VM is added after 3 readings.
2. Set the workload to **Low**. CPU drops and VMs are removed one by one (at least 1 stays).
3. Change the cooldown / confirm checks and see how the behaviour changes.

## API endpoints

| Method | URL | Purpose |
|---|---|---|
| GET | `/api/state` | Full current state |
| POST | `/api/tick` | One monitoring cycle (body: `{"autoscale": true}`) |
| POST | `/api/workload` | `{"level": "low\|medium\|high"}` |
| POST | `/api/vms` | New VM `{name, cpu, memory_mb}` |
| POST | `/api/vms/<id>/start` , `/stop` | Start / stop a VM |
| PUT | `/api/vms/<id>/config` | Change CPU / memory |
| DELETE | `/api/vms/<id>` | Delete a VM |
| PUT | `/api/settings` | Auto-scaler settings |
| POST | `/api/reset` | Reset the cloud |

## Production mode (everything from Flask only)

```bash
cd frontend && npm run build        # creates frontend/dist
cd ../backend && python app.py      # dashboard + API at http://127.0.0.1:5001
```

## What changed from the notebook

- `print()` calls were replaced with returned data, so the frontend can use it.
- On scale-up, a **stopped VM is started first**; otherwise a new VM is created (so scaling still works when the cloud limit is full).
- Default cooldown changed from 60 to **20 seconds** so the demo is quicker. You can change it in the dashboard.
- If all VMs are stopped or deleted and the auto-scaler is ON, one VM is started again.
