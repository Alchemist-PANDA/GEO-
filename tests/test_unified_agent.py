import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from geo_audit_agent.agents.unified_competitor_agent import UnifiedCompetitorIntelligenceAgent

@pytest.fixture
def agent():
    return UnifiedCompetitorIntelligenceAgent(correlation_id="test_123")

def test_discover_competitors(agent):
    mock_response = MagicMock()
    mock_response.content = '[{"name": "Burger King", "website": "https://burgerking.com", "source": "Google"}]'
    
    with patch('geo_audit_agent.agents.unified_competitor_agent.query_provider', return_value=mock_response):
        competitors = agent.discover_competitors("Burger Hub", "fast food", "Islamabad", limit=1)
        
        assert len(competitors) == 1
        assert competitors[0]["name"] == "Burger King"

@pytest.mark.asyncio
async def test_crawl_website(agent):
    mock_html = "<html><head><meta name='description' content='Test'></head><body></body></html>"
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = mock_html
    
    # Mock httpx.AsyncClient
    mock_client_instance = AsyncMock()
    mock_client_instance.get.return_value = mock_resp
    
    mock_client_context = AsyncMock()
    mock_client_context.__aenter__.return_value = mock_client_instance
    
    with patch('httpx.AsyncClient', return_value=mock_client_context):
        result = await agent.crawl_website("https://example.com")
        
        assert result["status"] == "success"
        assert result["url"] == "https://example.com"
        assert result["meta"].get("description") == "Test"

def test_analyze_competitor(agent):
    crawl_data = {
        "status": "success",
        "url": "https://example.com",
        "html": "A" * 4000,  # 4000 chars -> content_score 2
        "structured_data": {
            "json-ld": [{}, {}], # 2 items -> 50 score
            "microdata": [{}] # 1 item -> 10 score
        }
    }
    
    scores = agent.analyze_competitor(crawl_data)
    
    assert scores["schema"] == 60  # (2 * 25) + (1 * 10)
    assert scores["content"] == 2  # 4000 / 2000
    assert "authority" in scores

def test_generate_intelligence(agent):
    mock_response = MagicMock()
    mock_response.content = '{"explanation": "Better schema", "strategy": "Add JSON-LD"}'
    
    scores = {
        "authority": 90, "schema": 100, "content": 80, 
        "reviews": 95, "entities": 85, "citations": 88, "brand": 92
    }
    
    with patch('geo_audit_agent.agents.unified_competitor_agent.query_provider', return_value=mock_response):
        intel = agent.generate_intelligence("Competitor A", scores, "My Brand")
        
        assert intel["explanation"] == "Better schema"
        assert intel["strategy"] == "Add JSON-LD"

def test_generate_summary(agent):
    mock_response = MagicMock()
    mock_response.content = '{"insights": ["Insight 1"], "recommendations": ["Rec 1"], "projected_growth": "High"}'
    
    with patch('geo_audit_agent.agents.unified_competitor_agent.query_provider', return_value=mock_response):
        summary = agent.generate_summary("My Brand", [{"competitor": "Comp A"}])
        
        assert len(summary["insights"]) == 1
        assert summary["projected_growth"] == "High"
