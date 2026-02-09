"""
Alerts API endpoints for fetching generated critical alerts
"""

from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta
from typing import List, Optional

from agents.rag_agent import RAGAgent
from agents.financial_agent import FinancialAgent
from agents.alert_agent import AlertAgent
from agents.schemas import RAGQuery, FinancialAgentInput, AlertAgentInput, AlertConfig
from etl.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/alerts", tags=["alerts"])

# Initialize agents
_rag_agent = RAGAgent()
_financial_agent = FinancialAgent()
_alert_agent = AlertAgent()

# In-memory alert storage (for MVP)
# In production: use database (PostgreSQL with GeneratedAlert model)
_generated_alerts = []


def analyze_company_for_alerts(company_code: str, company_name: str) -> List[dict]:
    """
    Analyze a single company for critical alerts

    Process:
    1. Query RAG for latest financial data
    2. Extract metrics via FinancialAgent
    3. Evaluate against thresholds via AlertAgent
    4. Return HIGH severity alerts only
    """
    try:
        logger.info(f"Analyzing {company_name} ({company_code}) for alerts...")

        # Step 1: Retrieve financial documents from RAG
        query = f"Financial metrics and analysis for {company_name}"
        rag_output = _rag_agent.retrieve(RAGQuery(query=query))

        if not rag_output or not rag_output.text_chunks:
            logger.warning(f"No financial data found for {company_code}")
            return []

        # Step 2: Extract financial metrics
        financial_input = FinancialAgentInput(
            query=query,
            context={"rag_output": rag_output.dict()},
        )
        financial_output = _financial_agent.analyze(financial_input)

        if not financial_output or not financial_output.metrics:
            logger.warning(f"No metrics extracted for {company_code}")
            return []

        # Step 3: Evaluate alerts based on metrics
        alert_input = AlertAgentInput(
            query=query,
            company_code=company_code,
            company_name=company_name,
            financial_metrics=financial_output.metrics,
            rag_output=rag_output,
            config=AlertConfig(),
        )

        alert_output = _alert_agent.evaluate(alert_input)

        # Step 4: Filter HIGH severity alerts only
        critical_alerts = [a for a in alert_output.alerts if a.severity == "high"]

        logger.info(f"Generated {len(critical_alerts)} critical alerts for {company_code}")

        # Convert to dict format for API response
        return [
            {
                "alert_id": alert.alert_id,
                "company_code": alert.company_code,
                "company_name": alert.company_name,
                "severity": alert.severity,
                "alert_type": alert.alert_type,
                "reason": alert.reason,
                "triggered_at": datetime.utcnow().isoformat(),
                "evidence": [
                    {
                        "source": e.source if hasattr(e, 'source') else "Unknown",
                        "link": e.link if hasattr(e, 'link') else "#",
                        "page": e.page if hasattr(e, 'page') else None,
                        "excerpt": e.excerpt if hasattr(e, 'excerpt') else "",
                    }
                    for e in alert.evidence
                ] if alert.evidence else [],
            }
            for alert in critical_alerts
        ]

    except Exception as e:
        logger.error(f"Error analyzing {company_code}: {str(e)}")
        return []


@router.get("/critical")
async def get_critical_alerts(
    since_minutes: int = Query(60, description="Fetch alerts from last N minutes"),
    limit: int = Query(20, description="Maximum number of alerts to return"),
    unnotified_only: bool = Query(True, description="Only return alerts not yet notified to frontend"),
    use_real_analysis: bool = Query(False, description="Use real financial analysis (slower, may have 0 results)"),
) -> dict:
    """
    Fetch critical (HIGH severity) alerts from background monitoring

    Returns alerts that were:
    1. Generated in the last N minutes
    2. HIGH severity only
    3. Not yet sent to frontend (optional)

    Query Parameters:
    - since_minutes: How far back to look (default: 60 minutes)
    - limit: Max alerts to return (default: 20)
    - unnotified_only: Only unnotified alerts (default: true)

    Returns:
    {
        "alerts": [
            {
                "alert_id": "...",
                "company_code": "1155",
                "company_name": "Malayan Banking Berhad",
                "severity": "high",
                "alert_type": "Credit Risk Deterioration",
                "reason": "NPL ratio exceeded threshold",
                "triggered_at": "2026-02-06T12:34:56Z",
                "evidence": [...]
            }
        ],
        "total": 5,
        "timestamp": "2026-02-06T12:35:00Z"
    }
    """
    try:
        # TODO: Replace with database query
        # from etl.db.models import GeneratedAlert
        # session = get_db_session()
        # cutoff_time = datetime.utcnow() - timedelta(minutes=since_minutes)
        # query = session.query(GeneratedAlert).filter(
        #     GeneratedAlert.triggered_at >= cutoff_time,
        #     GeneratedAlert.severity == "high"
        # )
        # if unnotified_only:
        #     query = query.filter(GeneratedAlert.is_notified == False)
        # alerts = query.order_by(GeneratedAlert.triggered_at.desc()).limit(limit).all()

        all_alerts = []

        if use_real_analysis:
            # Real analysis mode (slower, depends on data extraction)
            companies_to_analyze = [
                ("FOODIE", "Foodie Media Berhad"),
                ("MAYBANK", "Malayan Banking Berhad"),
                ("AXIATA", "Axiata Group Berhad"),
                ("HLBANK", "Hong Leong Bank Berhad"),
                ("CIMB", "CIMB Group Holdings Berhad"),
            ]

            logger.info(f"Analyzing {len(companies_to_analyze)} companies for alerts...")

            for company_code, company_name in companies_to_analyze:
                try:
                    company_alerts = analyze_company_for_alerts(company_code, company_name)
                    all_alerts.extend(company_alerts)
                except Exception as e:
                    logger.error(f"Failed to analyze {company_name}: {str(e)}")
                    continue
        else:
            # Demo mode - return synthetic alerts for UI testing
            all_alerts = [
                {
                    "alert_id": "ALERT_FOODIE_001",
                    "company_code": "FOODIE",
                    "company_name": "Foodie Media Berhad",
                    "severity": "high",
                    "alert_type": "High Leverage Risk",
                    "reason": "Debt-to-Equity ratio of 1.8x exceeds safe threshold of 1.0x",
                    "triggered_at": datetime.utcnow().isoformat(),
                    "evidence": [
                        {
                            "source": "Q1 2025 Financial Statements",
                            "link": "/filings/foodie001",
                            "page": 12,
                            "excerpt": "Total debt increased to RM45M..."
                        }
                    ],
                },
                {
                    "alert_id": "ALERT_MAYBANK_001",
                    "company_code": "MAYBANK",
                    "company_name": "Malayan Banking Berhad",
                    "severity": "high",
                    "alert_type": "Credit Risk Deterioration",
                    "reason": "NPL ratio increased to 1.8% from 1.5%",
                    "triggered_at": (datetime.utcnow() - timedelta(seconds=45)).isoformat(),
                    "evidence": [
                        {
                            "source": "Q4 2025 Financial Report",
                            "link": "/filings/maybank001",
                            "page": 8,
                            "excerpt": "Impaired loans increased..."
                        }
                    ],
                },
                {
                    "alert_id": "ALERT_AXIATA_001",
                    "company_code": "AXIATA",
                    "company_name": "Axiata Group Berhad",
                    "severity": "high",
                    "alert_type": "Material Impairment",
                    "reason": "Asset impairment of RM1.2 billion identified",
                    "triggered_at": (datetime.utcnow() - timedelta(seconds=90)).isoformat(),
                    "evidence": [
                        {
                            "source": "Myanmar Operations Update",
                            "link": "/filings/axiata001",
                            "page": 3,
                            "excerpt": "Impairment charge..."
                        }
                    ],
                },
                {
                    "alert_id": "ALERT_CIMB_001",
                    "company_code": "CIMB",
                    "company_name": "CIMB Group Holdings Berhad",
                    "severity": "high",
                    "alert_type": "Declining Profitability",
                    "reason": "Net profit margin dropped to 8% from 12% YoY",
                    "triggered_at": (datetime.utcnow() - timedelta(seconds=60)).isoformat(),
                    "evidence": [
                        {
                            "source": "Q1 2025 Income Statement",
                            "link": "/filings/cimb001",
                            "page": 5,
                            "excerpt": "Operating expenses increased..."
                        }
                    ],
                },
                {
                    "alert_id": "ALERT_HLBANK_001",
                    "company_code": "HLBANK",
                    "company_name": "Hong Leong Bank Berhad",
                    "severity": "high",
                    "alert_type": "Poor Liquidity",
                    "reason": "Current ratio fell below 1.0 threshold",
                    "triggered_at": (datetime.utcnow() - timedelta(seconds=30)).isoformat(),
                    "evidence": [
                        {
                            "source": "Balance Sheet Q1 2025",
                            "link": "/filings/hlbank001",
                            "page": 2,
                            "excerpt": "Current assets declined..."
                        }
                    ],
                },
            ]

        # Sort by triggered_at (most recent first)
        all_alerts.sort(
            key=lambda x: x.get("triggered_at", ""), reverse=True
        )

        # Apply limit
        all_alerts = all_alerts[:limit]

        return {
            "alerts": all_alerts,
            "total": len(all_alerts),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error fetching critical alerts: {str(e)}")
        return {
            "alerts": [],
            "total": 0,
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
        }


@router.post("/acknowledge/{alert_id}")
async def acknowledge_alert(alert_id: str) -> dict:
    """
    Mark an alert as notified to prevent re-sending to frontend

    Args:
        alert_id: ID of alert to acknowledge

    Returns:
    {
        "alert_id": "...",
        "status": "notified",
        "notified_at": "2026-02-06T12:35:00Z"
    }
    """
    try:
        # TODO: Update database
        # session = get_db_session()
        # alert = session.query(GeneratedAlert).filter_by(alert_id=alert_id).first()
        # if alert:
        #     alert.is_notified = True
        #     alert.notified_at = datetime.utcnow()
        #     session.commit()

        return {
            "alert_id": alert_id,
            "status": "notified",
            "notified_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error acknowledging alert {alert_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company/{company_code}")
async def get_company_alerts(
    company_code: str,
    severity: str = Query("high", description="Alert severity filter: high, medium, low, or all"),
) -> dict:
    """
    Fetch alerts for a specific company

    Args:
        company_code: Company code (e.g., "FOODIE", "MAYBANK")
        severity: Filter by severity (default: "high" for critical only)

    Returns:
    {
        "company_code": "FOODIE",
        "alerts": [
            {
                "alert_id": "...",
                "severity": "high",
                "alert_type": "...",
                "reason": "...",
                ...
            }
        ],
        "total": 3,
        "critical_count": 3
    }
    """
    try:
        # Map company codes to names for analysis
        company_map = {
            "FOODIE": "Foodie Media Berhad",
            "MAYBANK": "Malayan Banking Berhad",
            "AXIATA": "Axiata Group Berhad",
            "HLBANK": "Hong Leong Bank Berhad",
            "CIMB": "CIMB Group Holdings Berhad",
            "1155": "Malayan Banking Berhad",
            "6888": "Axiata Group Berhad",
            "1082": "Hong Leong Bank Berhad",
        }

        company_name = company_map.get(company_code.upper(), company_code)

        logger.info(f"Fetching alerts for {company_name} ({company_code})...")

        # Demo alerts data - in production, query from database
        all_company_alerts = {
            "FOODIE": [
                {
                    "alert_id": "ALERT_FOODIE_001",
                    "company_code": "FOODIE",
                    "company_name": "Foodie Media Berhad",
                    "severity": "high",
                    "alert_type": "High Leverage Risk",
                    "reason": "Debt-to-Equity ratio of 1.8x exceeds safe threshold of 1.0x",
                    "triggered_at": datetime.utcnow().isoformat(),
                    "status": "active",
                    "evidence": [{"source": "Q1 2025 Financial Statements", "link": "/filings/foodie001", "page": 12, "excerpt": "Total debt increased to RM45M..."}],
                },
                {
                    "alert_id": "ALERT_FOODIE_002",
                    "company_code": "FOODIE",
                    "company_name": "Foodie Media Berhad",
                    "severity": "high",
                    "alert_type": "Declining Profitability",
                    "reason": "Net profit margin dropped to 8% from 12% YoY",
                    "triggered_at": (datetime.utcnow() - timedelta(seconds=45)).isoformat(),
                    "status": "active",
                    "evidence": [{"source": "Q1 2025 Income Statement", "link": "/filings/foodie002", "page": 8, "excerpt": "Operating expenses increased significantly..."}],
                },
                {
                    "alert_id": "ALERT_FOODIE_003",
                    "company_code": "FOODIE",
                    "company_name": "Foodie Media Berhad",
                    "severity": "high",
                    "alert_type": "Poor Cash Flow",
                    "reason": "Operating cash flow negative for 2 consecutive quarters",
                    "triggered_at": (datetime.utcnow() - timedelta(seconds=90)).isoformat(),
                    "status": "active",
                    "evidence": [{"source": "Cash Flow Statement Q1 2025", "link": "/filings/foodie003", "page": 15, "excerpt": "Cash outflows exceeded inflows..."}],
                },
            ],
            "MAYBANK": [
                {
                    "alert_id": "ALERT_MAYBANK_001",
                    "company_code": "MAYBANK",
                    "company_name": "Malayan Banking Berhad",
                    "severity": "high",
                    "alert_type": "Credit Risk Deterioration",
                    "reason": "NPL ratio increased to 1.8% from 1.5%",
                    "triggered_at": (datetime.utcnow() - timedelta(seconds=30)).isoformat(),
                    "status": "active",
                    "evidence": [{"source": "Q4 2025 Financial Report", "link": "/filings/maybank001", "page": 8, "excerpt": "Impaired loans increased..."}],
                },
            ],
            "AXIATA": [
                {
                    "alert_id": "ALERT_AXIATA_001",
                    "company_code": "AXIATA",
                    "company_name": "Axiata Group Berhad",
                    "severity": "high",
                    "alert_type": "Material Impairment",
                    "reason": "Asset impairment of RM1.2 billion identified",
                    "triggered_at": (datetime.utcnow() - timedelta(seconds=60)).isoformat(),
                    "status": "active",
                    "evidence": [{"source": "Myanmar Operations Update", "link": "/filings/axiata001", "page": 3, "excerpt": "Impairment charge of RM1.2B..."}],
                },
            ],
            "CIMB": [
                {
                    "alert_id": "ALERT_CIMB_001",
                    "company_code": "CIMB",
                    "company_name": "CIMB Group Holdings Berhad",
                    "severity": "high",
                    "alert_type": "Declining Profitability",
                    "reason": "Net profit margin dropped to 8% from 12% YoY",
                    "triggered_at": (datetime.utcnow() - timedelta(seconds=60)).isoformat(),
                    "status": "active",
                    "evidence": [{"source": "Q1 2025 Income Statement", "link": "/filings/cimb001", "page": 5, "excerpt": "Operating expenses increased..."}],
                },
            ],
            "HLBANK": [
                {
                    "alert_id": "ALERT_HLBANK_001",
                    "company_code": "HLBANK",
                    "company_name": "Hong Leong Bank Berhad",
                    "severity": "high",
                    "alert_type": "Poor Liquidity",
                    "reason": "Current ratio fell below 1.0 threshold",
                    "triggered_at": (datetime.utcnow() - timedelta(seconds=45)).isoformat(),
                    "status": "active",
                    "evidence": [{"source": "Balance Sheet Q1 2025", "link": "/filings/hlbank001", "page": 2, "excerpt": "Current assets declined..."}],
                },
            ],
        }

        # Get alerts for this company
        company_alerts = all_company_alerts.get(company_code.upper(), [])

        # Filter by severity if needed
        if severity.lower() != "all":
            company_alerts = [a for a in company_alerts if a["severity"] == severity.lower()]

        # Count critical alerts
        critical_count = len([a for a in company_alerts if a["severity"] == "high"])

        return {
            "company_code": company_code,
            "company_name": company_name,
            "alerts": company_alerts,
            "total": len(company_alerts),
            "critical_count": critical_count,
        }

    except Exception as e:
        logger.error(f"Error fetching alerts for {company_code}: {str(e)}")
        return {
            "company_code": company_code,
            "alerts": [],
            "total": 0,
            "critical_count": 0,
            "error": str(e),
        }


@router.get("/stats")
async def get_alert_stats() -> dict:
    """
    Get alert statistics

    Returns:
    {
        "total_high_severity": 5,
        "total_medium_severity": 8,
        "total_low_severity": 12,
        "unnotified_high": 2,
        "companies_with_alerts": ["1155", "1082", "6888"],
        "last_check_time": "2026-02-06T12:35:00Z"
    }
    """
    try:
        # TODO: Query database for statistics
        # session = get_db_session()
        # high = session.query(GeneratedAlert).filter_by(severity="high").count()
        # medium = session.query(GeneratedAlert).filter_by(severity="medium").count()
        # low = session.query(GeneratedAlert).filter_by(severity="low").count()
        # unnotified_high = session.query(GeneratedAlert).filter_by(
        #     severity="high", is_notified=False
        # ).count()
        # companies = session.query(GeneratedAlert.company_code).distinct()

        return {
            "total_high_severity": 0,
            "total_medium_severity": 0,
            "total_low_severity": 0,
            "unnotified_high": 0,
            "companies_with_alerts": [],
            "last_check_time": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error fetching alert stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
