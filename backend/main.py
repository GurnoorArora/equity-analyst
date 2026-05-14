from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import json
import os
from dotenv import load_dotenv

from models.schemas import StockQuery, AnalysisReport, AgentState
from orchestrator import EquityAnalystWorkflow

# Load environment variables
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    print("🚀 Starting AI Equity Research Analyst...")
    
    # Create data directories
    os.makedirs("./data/annual_reports", exist_ok=True)
    os.makedirs("./data/outputs", exist_ok=True)
    os.makedirs("./data/chroma_db", exist_ok=True)
    
    yield
    
    # Shutdown
    print("📊 Shutting down AI Equity Research Analyst...")


app = FastAPI(
    title="AI Equity Research Analyst",
    description="Intelligent multiagent system for Indian stock market research",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConnectionManager:
    """Manages WebSocket connections for live agent updates"""
    
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def send_update(self, message: dict):
        """Send update to all connected clients"""
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                # Remove disconnected clients
                self.active_connections.remove(connection)


manager = ConnectionManager()


@app.get("/")
async def root():
    return {
        "message": "AI Equity Research Analyst API",
        "version": "1.0.0",
        "status": "active"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "agents": "ready"}


@app.post("/analyze", response_model=AnalysisReport)
async def analyze_stocks(query: StockQuery):
    """
    Main endpoint for stock analysis
    Supports three modes: analyze_stock, get_recommendations, explore_relationships
    """
    try:
        # Initialize the LangGraph workflow
        workflow = EquityAnalystWorkflow()
        
        # Create initial state
        initial_state = AgentState(query=query)
        
        # Send initial update
        await manager.send_update({
            "type": "analysis_started",
            "query": query.query,
            "mode": query.mode
        })
        
        # Execute the workflow
        final_state = await workflow.run(initial_state, manager)
        
        if not final_state.final_report:
            raise HTTPException(status_code=500, detail="Analysis failed to generate report")
        
        # Send completion update
        await manager.send_update({
            "type": "analysis_completed",
            "report": final_state.final_report.dict()
        })
        
        return final_state.final_report
        
    except Exception as e:
        await manager.send_update({
            "type": "analysis_error",
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for live agent progress updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            # Echo back for heartbeat
            await websocket.send_text(f"Received: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get("/stocks/universe")
async def get_stock_universe():
    """Get list of all stocks in the analysis universe (Nifty 50 + Midcap 150)"""
    # This will be implemented with Universe Agent
    return {"message": "Stock universe endpoint - to be implemented"}


@app.get("/stocks/{symbol}/quick-info")
async def get_quick_stock_info(symbol: str):
    """Get quick market data for a specific stock"""
    # This will use Market Agent directly
    return {"message": f"Quick info for {symbol} - to be implemented"}


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )