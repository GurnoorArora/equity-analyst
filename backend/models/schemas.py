from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class QueryMode(str, Enum):
    ANALYZE_STOCK = "analyze_stock"
    GET_RECOMMENDATIONS = "get_recommendations"
    EXPLORE_RELATIONSHIPS = "explore_relationships"


class StockQuery(BaseModel):
    query: str = Field(..., description="User's investment query")
    mode: QueryMode = Field(..., description="Type of analysis requested")
    stock_symbol: Optional[str] = Field(None, description="Specific stock symbol if analyzing single stock")


class AgentFindings(BaseModel):
    agent_name: str = Field(..., description="Name of the agent")
    findings: Dict[str, Any] = Field(..., description="Agent's analysis results")
    red_flags: List[str] = Field(default_factory=list, description="Risk indicators found")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score 0-1")
    citations: List[str] = Field(default_factory=list, description="Sources referenced")


class MarketData(BaseModel):
    symbol: str
    current_price: float
    price_change: float
    price_change_percent: float
    volume: int
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None


class NewsItem(BaseModel):
    title: str
    url: str
    published_date: str
    sentiment: str  # "positive", "negative", "neutral"
    sentiment_score: float = Field(ge=-1, le=1)


class FundamentalData(BaseModel):
    symbol: str
    revenue_growth: Optional[float] = None
    profit_growth: Optional[float] = None
    debt_to_equity: Optional[float] = None
    roe: Optional[float] = None
    promoter_holding: Optional[float] = None


class CompanyRelationship(BaseModel):
    from_company: str
    to_company: str
    relationship_type: str  # "supplier", "customer", "subsidiary", "joint_venture", etc.
    details: str
    source_page: Optional[str] = None


class StockRecommendation(BaseModel):
    symbol: str
    company_name: str
    recommendation: str  # "Strong Buy", "Buy", "Hold", "Sell", "Strong Sell"
    target_price: Optional[float] = None
    reasoning: str
    key_risks: List[str]
    confidence: float = Field(ge=0, le=1)
    market_data: MarketData
    fundamental_data: Optional[FundamentalData] = None
    recent_news: List[NewsItem] = Field(default_factory=list)
    graph_insights: List[CompanyRelationship] = Field(default_factory=list)


class AnalysisReport(BaseModel):
    query: str
    mode: QueryMode
    recommendations: List[StockRecommendation]
    overall_market_view: str
    portfolio_notes: List[str] = Field(default_factory=list)
    generated_at: str
    processing_time_seconds: float


class AgentState(BaseModel):
    """Shared state across all LangGraph agents"""
    query: StockQuery
    stock_symbols: List[str] = Field(default_factory=list)
    agent_findings: Dict[str, AgentFindings] = Field(default_factory=dict)
    market_data: Dict[str, MarketData] = Field(default_factory=dict)
    news_data: Dict[str, List[NewsItem]] = Field(default_factory=dict)
    fundamental_data: Dict[str, FundamentalData] = Field(default_factory=dict)
    graph_insights: List[CompanyRelationship] = Field(default_factory=list)
    red_flags_found: bool = False
    final_report: Optional[AnalysisReport] = None
    processing_steps: List[str] = Field(default_factory=list)


class AgentResponse(BaseModel):
    """Standard response format for all agents"""
    success: bool
    data: Dict[str, Any]
    errors: List[str] = Field(default_factory=list)
    next_agents: List[str] = Field(default_factory=list, description="Agents to run next")
    processing_time: float
