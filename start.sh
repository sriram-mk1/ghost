#!/bin/bash

# ============================================
# Ghost Teammate - Startup Script
# ============================================
# This script starts all required services:
# 1. Temporal Server (workflow orchestration)
# 2. Backend API (FastAPI)
# 3. Temporal Worker (executes workflows)
# 4. Frontend (Next.js)
# 5. ngrok (exposes webhooks to internet)
#
# Usage:
#   chmod +x start.sh
#   ./start.sh
#
# To stop: Press Ctrl+C (kills all background processes)
# ============================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

PROJECT_DIR="/Users/sriram.mk/Downloads/ghost"
cd "$PROJECT_DIR"

# Load environment variables
if [ -f "backend/.env" ]; then
    export $(grep -v '^#' backend/.env | xargs)
    echo -e "${GREEN}✓ Loaded backend/.env${NC}"
fi

echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║           🚀 Ghost Teammate Startup Script             ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Track PIDs for cleanup
PIDS=()

cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Shutting down all services...${NC}"
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
        fi
    done
    # Kill any remaining processes
    pkill -f "temporal server" 2>/dev/null || true
    pkill -f "uvicorn backend.main" 2>/dev/null || true
    pkill -f "python -m backend.worker" 2>/dev/null || true
    pkill -f "next dev" 2>/dev/null || true
    pkill -f "ngrok http" 2>/dev/null || true
    echo -e "${GREEN}✓ All services stopped${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# ============================================
# 1. Check Prerequisites
# ============================================
echo -e "${BLUE}[1/5]${NC} Checking prerequisites..."

if ! command -v temporal &> /dev/null; then
    echo -e "${RED}❌ Temporal CLI not found. Install with: brew install temporal${NC}"
    exit 1
fi

if ! command -v ngrok &> /dev/null; then
    echo -e "${YELLOW}⚠️  ngrok not found. Webhooks won't work without it.${NC}"
    echo -e "${YELLOW}   Install with: brew install ngrok${NC}"
    SKIP_NGROK=true
fi

if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Python venv not found. Run: python3 -m venv venv && source venv/bin/activate && pip install -r backend/requirements.txt${NC}"
    exit 1
fi

if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}⚠️  Frontend dependencies not installed. Installing...${NC}"
    cd frontend && npm install && cd ..
fi

echo -e "${GREEN}✓ Prerequisites OK${NC}"
echo ""

# ============================================
# 2. Start Temporal Server
# ============================================
echo -e "${BLUE}[2/5]${NC} Starting Temporal Server..."

# Check if Temporal is already running
if lsof -i :7233 &> /dev/null; then
    echo -e "${YELLOW}   Temporal already running on port 7233${NC}"
else
    temporal server start-dev --db-filename temporal.db --log-level warn &
    PIDS+=($!)
    sleep 3
    echo -e "${GREEN}✓ Temporal Server started (http://localhost:8233)${NC}"
fi
echo ""

# ============================================
# 3. Start Backend API
# ============================================
echo -e "${BLUE}[3/5]${NC} Starting Backend API..."

source venv/bin/activate
export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"

# Check if backend is already running
if lsof -i :8000 &> /dev/null; then
    echo -e "${YELLOW}   Backend already running on port 8000${NC}"
else
    uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
    PIDS+=($!)
    sleep 2
    echo -e "${GREEN}✓ Backend API started (http://localhost:8000)${NC}"
fi
echo ""

# ============================================
# 4. Start Temporal Worker
# ============================================
echo -e "${BLUE}[4/5]${NC} Starting Temporal Worker..."

python -m backend.worker &
PIDS+=($!)
sleep 2
echo -e "${GREEN}✓ Temporal Worker started${NC}"
echo ""

# ============================================
# 5. Start Frontend
# ============================================
echo -e "${BLUE}[5/5]${NC} Starting Frontend..."

cd frontend

# Check if frontend is already running
if lsof -i :3000 &> /dev/null; then
    echo -e "${YELLOW}   Frontend already running on port 3000${NC}"
else
    npm run dev &
    PIDS+=($!)
    sleep 3
    echo -e "${GREEN}✓ Frontend started (http://localhost:3000)${NC}"
fi

cd ..
echo ""

# ============================================
# 6. Start ngrok (optional)
# ============================================
if [ "$SKIP_NGROK" != "true" ]; then
    echo -e "${BLUE}[Bonus]${NC} Starting ngrok tunnel..."
    
    # Check for static domain in environment
    if [ -n "$NGROK_DOMAIN" ]; then
        echo -e "${YELLOW}   Using static domain: $NGROK_DOMAIN${NC}"
        ngrok http 8000 --domain="$NGROK_DOMAIN" --log=stdout > /tmp/ngrok.log 2>&1 &
    else
        ngrok http 8000 --log=stdout > /tmp/ngrok.log 2>&1 &
    fi
    
    PIDS+=($!)
    sleep 3
    
    # Extract ngrok URL
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"[^"]*"' | head -1 | cut -d'"' -f4)
    if [ -n "$NGROK_URL" ]; then
        echo -e "${GREEN}✓ ngrok tunnel: ${CYAN}$NGROK_URL${NC}"
        echo ""
        echo -e "${YELLOW}📧 Set this as your Resend webhook URL:${NC}"
        echo -e "   ${CYAN}$NGROK_URL/webhooks/resend/inbound${NC}"
    else
        echo -e "${YELLOW}⚠️  Could not get ngrok URL. Check http://localhost:4040${NC}"
    fi
fi

echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║              🎉 All Services Running!                  ║${NC}"
echo -e "${CYAN}╠════════════════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}║${NC}  Frontend:    ${GREEN}http://localhost:3000${NC}                   ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}  Backend:     ${GREEN}http://localhost:8000${NC}                   ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}  Temporal UI: ${GREEN}http://localhost:8233${NC}                   ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}  ngrok:       ${GREEN}http://localhost:4040${NC}                   ${CYAN}║${NC}"
echo -e "${CYAN}╠════════════════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}║${NC}  Press ${RED}Ctrl+C${NC} to stop all services                  ${CYAN}║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Keep script running and wait for Ctrl+C
wait

