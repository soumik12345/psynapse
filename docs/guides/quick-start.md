# Psynapse Quick Start Guide

## Install Psynapse

First, clone the repository and navigate to the project directory:

```bash
git clone https://github.com/soumik12345/psynapse-web
cd psynapse-web
```

Then, install the backend dependencies:

```bash
uv venv
source .venv/bin/activate
uv pip install .
```

Finally, install the frontend dependencies:

```bash
cd frontend
npm install
```

## 🚀 Get Started in 3 Steps

### Step 1: Start the Backend
Open a terminal and run:
```bash
uv run psynapse-backend
```

You should see:
```
Starting Psynapse backend server on http://localhost:8000...
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 2: Start the Frontend
Open another terminal and run:
```bash
./start-frontend.sh
```

You should see:
```
Starting Psynapse frontend development server...
VITE ready in XXX ms
➜  Local:   http://localhost:5173/
```

### Step 3: Open Your Browser
Navigate to: **http://localhost:5173**

## 🎯 First Workflow

Create your first workflow in 30 seconds:

1. **Drag an "add" node** from the left panel onto the canvas
2. **Enter values** in the node: `a=10`, `b=5`
3. **Drag a "ViewNode"** onto the canvas
4. **Connect** the output (right side) of the add node to the input (left side) of the ViewNode
5. **Click "Execute"** button (top-right)
6. **See the result**: ViewNode shows `15`

## 📝 Tips

- **Connect nodes**: Drag from output socket (right) to input socket (left)
- **Input values**: Type directly or connect from another node
- **Multiple ViewNodes**: Add multiple ViewNodes to inspect different parts of your workflow
- **Minimap**: Use the minimap (bottom-right) to navigate large workflows
- **Canvas controls**: Scroll to zoom, drag to pan

## 🧪 Example: Calculator

Create `(5 + 3) × (2 + 4) = 48`:

1. Drag **2 "add" nodes** onto canvas
   - First add: `a=5`, `b=3`
   - Second add: `a=2`, `b=4`
2. Drag **1 "multiply" node** onto canvas
3. Connect:
   - First add output → multiply's `a` input
   - Second add output → multiply's `b` input
4. Drag **ViewNode** and connect multiply output to it
5. Click **Execute**
6. Result: **48**

## 🔧 Troubleshooting

### Backend won't start
```bash
cd backend
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
uv run python main.py
```

### Frontend won't start
```bash
cd frontend
npm install
npm run dev
```
