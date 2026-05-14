from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
import asyncio
from datetime import datetime

from models.schemas import AgentState, AgentResponse, AnalysisReport
from agents.market_agent import MarketAgent
from agents.news_agent import NewsAgent
from agents.fundamental_agent import FundamentalAgent
from agents.graph_query_agent import GraphQueryAgent
from agents.risk_agent import RiskAgent
from agents.critic_agent import CriticAgent
from agents.report_agent import ReportAgent


class EquityAnalystWorkflow:
    """
    LangGraph orchestrator for the equity research workflow
    Manages dynamic agent execution based on findings and conditions
    """
    
    def __init__(self):
        self.graph = self._build_graph()
        self.agents = {
            "market": MarketAgent(),
            "news": NewsAgent(),
            "fundamental": FundamentalAgent(),
            "graph_query": GraphQueryAgent(),
            "risk": RiskAgent(),
            "critic": CriticAgent(),
            "report": ReportAgent()
        }
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        
        # Create the state graph
        workflow = StateGraph(AgentState)
        
        # Add nodes for each agent
        workflow.add_node("start", self._start_analysis)
        workflow.add_node("parallel_analysis", self._run_parallel_analysis)
        workflow.add_node("risk_analysis", self._run_risk_analysis)
        workflow.add_node("critic_analysis", self._run_critic_analysis)
        workflow.add_node("generate_report", self._generate_final_report)
        
        # Define the workflow edges
        workflow.set_entry_point("start")
        
        # Start -> Parallel Analysis (Market, News, Fundamental, Graph)
        workflow.add_edge("start", "parallel_analysis")
        
        # Conditional edge: Parallel Analysis -> Risk Analysis (if red flags) or Critic Analysis
        workflow.add_conditional_edges(
            "parallel_analysis",
            self._should_run_risk_analysis,
            {
                "run_risk": "risk_analysis",
                "skip_risk": "critic_analysis"
            }
        )
        
        # Risk Analysis -> Critic Analysis
        workflow.add_edge("risk_analysis", "critic_analysis")
        
        # Critic Analysis -> Generate Report
        workflow.add_edge("critic_analysis", "generate_report")
        
        # Generate Report -> END
        workflow.add_edge("generate_report", END)
        
        return workflow.compile()
    
    async def _start_analysis(self, state: AgentState) -> AgentState:
        """Initialize the analysis workflow"""
        state.processing_steps.append(f"Started analysis at {datetime.now().isoformat()}")
        
        # Determine stock symbols based on query mode
        if state.query.mode == "analyze_stock" and state.query.stock_symbol:
            state.stock_symbols = [state.query.stock_symbol.upper()]
        elif state.query.mode == "get_recommendations":
            # For now, use a sample set - will be replaced with Screener Agent
            state.stock_symbols = ["RELIANCE.NS", "INFY.NS", "TITAN.NS"]
        else:  # explore_relationships
            # Extract symbols from query or use default set
            state.stock_symbols = ["RELIANCE.NS", "TCS.NS", "HDFC.NS"]
        
        state.processing_steps.append(f"Target stocks: {', '.join(state.stock_symbols)}")
        return state
    
    async def _run_parallel_analysis(self, state: AgentState) -> AgentState:
        """Run Market, News, Fundamental, and Graph agents in parallel"""
        state.processing_steps.append("Running parallel analysis: Market, News, Fundamental, Graph")
        
        # Create tasks for parallel execution
        tasks = []
        
        # Market Agent
        tasks.append(self._run_agent("market", state))
        
        # News Agent
        tasks.append(self._run_agent("news", state))
        
        # Fundamental Agent
        tasks.append(self._run_agent("fundamental", state))
        
        # Graph Query Agent (if we have relationships to explore)
        if state.query.mode in ["explore_relationships", "get_recommendations"]:
            tasks.append(self._run_agent("graph_query", state))
        
        # Execute all agents in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and update state
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                state.processing_steps.append(f"Agent {i} failed: {str(result)}")
            else:
                # Results are already integrated into state by individual agents
                pass
        
        # Check for red flags across all findings
        state.red_flags_found = any(
            len(findings.red_flags) > 0 
            for findings in state.agent_findings.values()
        )
        
        state.processing_steps.append(f"Parallel analysis complete. Red flags found: {state.red_flags_found}")
        return state
    
    async def _run_agent(self, agent_name: str, state: AgentState) -> AgentState:
        """Run a specific agent and update state"""
        try:
            agent = self.agents[agent_name]
            response = await agent.execute(state)
            
            if response.success:
                # Update state with agent findings
                state.agent_findings[agent_name] = response.data
                state.processing_steps.append(f"{agent_name.title()} Agent completed successfully")
            else:
                state.processing_steps.append(f"{agent_name.title()} Agent failed: {', '.join(response.errors)}")
                
        except Exception as e:
            state.processing_steps.append(f"{agent_name.title()} Agent error: {str(e)}")
        
        return state
    
    def _should_run_risk_analysis(self, state: AgentState) -> str:
        """Conditional logic to determine if Risk Agent should run"""
        if state.red_flags_found:
            return "run_risk"
        return "skip_risk"
    
    async def _run_risk_analysis(self, state: AgentState) -> AgentState:
        """Run Risk Agent for deep dive on red flags"""
        state.processing_steps.append("Running Risk Agent for red flag analysis")
        return await self._run_agent("risk", state)
    
    async def _run_critic_analysis(self, state: AgentState) -> AgentState:
        """Run Critic Agent to challenge the investment thesis"""
        state.processing_steps.append("Running Critic Agent to challenge thesis")
        return await self._run_agent("critic", state)
    
    async def _generate_final_report(self, state: AgentState) -> AgentState:
        """Generate the final investment report"""
        state.processing_steps.append("Generating final investment report")
        
        # Run Report Agent to synthesize all findings
        await self._run_agent("report", state)
        
        # The Report Agent should have populated state.final_report
        if not state.final_report:
            # Fallback: create a basic report structure
            state.final_report = AnalysisReport(
                query=state.query.query,
                mode=state.query.mode,
                recommendations=[],
                overall_market_view="Analysis completed with limited data",
                generated_at=datetime.now().isoformat(),
                processing_time_seconds=0.0
            )
        
        state.processing_steps.append("Final report generated successfully")
        return state
    
    async def run(self, initial_state: AgentState, connection_manager=None) -> AgentState:
        """
        Execute the complete workflow
        
        Args:
            initial_state: Initial state with user query
            connection_manager: Optional WebSocket manager for live updates
            
        Returns:
            Final state with completed analysis
        """
        start_time = datetime.now()
        
        try:
            # Send progress updates if connection manager provided
            if connection_manager:
                await connection_manager.send_update({
                    "type": "workflow_started",
                    "query": initial_state.query.query,
                    "mode": initial_state.query.mode
                })
            
            # Execute the workflow
            final_state = await self.graph.ainvoke(initial_state)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            if final_state.final_report:
                final_state.final_report.processing_time_seconds = processing_time
            
            # Send completion update
            if connection_manager:
                await connection_manager.send_update({
                    "type": "workflow_completed",
                    "processing_time": processing_time,
                    "steps_completed": len(final_state.processing_steps)
                })
            
            return final_state
            
        except Exception as e:
            # Send error update
            if connection_manager:
                await connection_manager.send_update({
                    "type": "workflow_error",
                    "error": str(e)
                })
            raise e
