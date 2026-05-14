from abc import ABC, abstractmethod
from typing import Dict, Any, List
import time
from datetime import datetime

from models.schemas import AgentState, AgentResponse, AgentFindings


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the equity research system
    Provides common functionality and enforces consistent interface
    """
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.start_time = None
    
    @abstractmethod
    async def _execute_logic(self, state: AgentState) -> Dict[str, Any]:
        """
        Core agent logic - must be implemented by each agent
        
        Args:
            state: Current workflow state
            
        Returns:
            Dict containing agent's findings and analysis
        """
        pass
    
    def _detect_red_flags(self, data: Dict[str, Any]) -> List[str]:
        """
        Detect potential red flags in the agent's findings
        Can be overridden by specific agents for custom red flag detection
        
        Args:
            data: Agent's analysis results
            
        Returns:
            List of red flag descriptions
        """
        return []
    
    def _calculate_confidence(self, data: Dict[str, Any]) -> float:
        """
        Calculate confidence score for the agent's findings
        Can be overridden by specific agents for custom confidence calculation
        
        Args:
            data: Agent's analysis results
            
        Returns:
            Confidence score between 0 and 1
        """
        return 0.8  # Default confidence
    
    def _get_citations(self, data: Dict[str, Any]) -> List[str]:
        """
        Extract citations/sources for the agent's findings
        Can be overridden by specific agents
        
        Args:
            data: Agent's analysis results
            
        Returns:
            List of citation strings
        """
        return []
    
    async def execute(self, state: AgentState) -> AgentResponse:
        """
        Main execution method for the agent
        Handles timing, error handling, and response formatting
        
        Args:
            state: Current workflow state
            
        Returns:
            Standardized agent response
        """
        self.start_time = time.time()
        errors = []
        
        try:
            # Execute the agent's core logic
            data = await self._execute_logic(state)
            
            # Detect red flags
            red_flags = self._detect_red_flags(data)
            
            # Calculate confidence
            confidence = self._calculate_confidence(data)
            
            # Get citations
            citations = self._get_citations(data)
            
            # Create agent findings
            findings = AgentFindings(
                agent_name=self.agent_name,
                findings=data,
                red_flags=red_flags,
                confidence=confidence,
                citations=citations
            )
            
            # Calculate processing time
            processing_time = time.time() - self.start_time
            
            return AgentResponse(
                success=True,
                data=findings.dict(),
                errors=[],
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = time.time() - self.start_time if self.start_time else 0
            error_msg = f"{self.agent_name} execution failed: {str(e)}"
            
            return AgentResponse(
                success=False,
                data={},
                errors=[error_msg],
                processing_time=processing_time
            )
    
    def _log_progress(self, message: str):
        """Log progress message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {self.agent_name}: {message}")
    
    def _format_currency(self, value: float) -> str:
        """Format currency values for Indian market"""
        if value >= 10000000:  # 1 crore
            return f"₹{value/10000000:.1f}Cr"
        elif value >= 100000:  # 1 lakh
            return f"₹{value/100000:.1f}L"
        else:
            return f"₹{value:,.0f}"
    
    def _format_percentage(self, value: float) -> str:
        """Format percentage values"""
        return f"{value:.1f}%"
