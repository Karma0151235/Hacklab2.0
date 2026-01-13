"""
Category-specific query helpers for different announcement types
Provides convenient functions for querying chunks by category
"""

from typing import List, Dict, Any
from sqlalchemy.orm import Session

from etl.db.models import (
    ShareholdingChunk, FinancialChunk, DividendChunk,
    CorporateActionChunk, MeetingChunk, DocumentChunkVector
)


# ============================================================================
# SHAREHOLDING QUERIES
# ============================================================================

def get_shareholding_by_shareholder(
    session: Session,
    shareholder_name: str,
    limit: int = 100
) -> List[ShareholdingChunk]:
    """Get shareholding chunks by shareholder name"""
    return session.query(ShareholdingChunk)\
        .filter_by(shareholder_name=shareholder_name)\
        .order_by(ShareholdingChunk.created_at.desc())\
        .limit(limit)\
        .all()


def get_shareholding_by_company(
    session: Session,
    company_code: str,
    limit: int = 100
) -> List[ShareholdingChunk]:
    """Get shareholding chunks by company code"""
    return session.query(ShareholdingChunk)\
        .filter_by(company_code=company_code)\
        .order_by(ShareholdingChunk.created_at.desc())\
        .limit(limit)\
        .all()


def get_shareholding_by_ticker(
    session: Session,
    ticker: str,
    limit: int = 100
) -> List[ShareholdingChunk]:
    """Get shareholding chunks by ticker symbol"""
    return session.query(ShareholdingChunk)\
        .filter_by(ticker=ticker)\
        .order_by(ShareholdingChunk.created_at.desc())\
        .limit(limit)\
        .all()


def get_major_shareholders(
    session: Session,
    company_code: str,
    threshold_percentage: float = 5.0
) -> List[ShareholdingChunk]:
    """Get major shareholders (above threshold) for a company"""
    return session.query(ShareholdingChunk)\
        .filter(
            ShareholdingChunk.company_code == company_code,
            ShareholdingChunk.current_percentage >= threshold_percentage
        )\
        .order_by(ShareholdingChunk.current_percentage.desc())\
        .all()


def get_shareholding_changes(
    session: Session,
    shareholder_name: str,
    company_code: str
) -> List[ShareholdingChunk]:
    """Get shareholding history for a shareholder in a company"""
    return session.query(ShareholdingChunk)\
        .filter(
            ShareholdingChunk.shareholder_name == shareholder_name,
            ShareholdingChunk.company_code == company_code
        )\
        .order_by(ShareholdingChunk.created_at.asc())\
        .all()


def get_pending_shareholding_embeddings(
    session: Session,
    limit: int = 100
) -> List[ShareholdingChunk]:
    """Get shareholding chunks pending embedding generation"""
    return session.query(ShareholdingChunk)\
        .filter_by(embedding_status="pending")\
        .order_by(ShareholdingChunk.created_at.asc())\
        .limit(limit)\
        .all()


# ============================================================================
# FINANCIAL QUERIES
# ============================================================================

def get_financial_by_metric(
    session: Session,
    metric_type: str,
    limit: int = 100
) -> List[FinancialChunk]:
    """Get financial chunks by metric type (Revenue, EPS, Profit, etc.)"""
    return session.query(FinancialChunk)\
        .filter_by(metric_type=metric_type)\
        .order_by(FinancialChunk.created_at.desc())\
        .limit(limit)\
        .all()


def get_financial_by_company(
    session: Session,
    company_code: str,
    limit: int = 100
) -> List[FinancialChunk]:
    """Get financial chunks for a company"""
    return session.query(FinancialChunk)\
        .filter_by(company_code=company_code)\
        .order_by(FinancialChunk.created_at.desc())\
        .limit(limit)\
        .all()


def get_financial_by_period(
    session: Session,
    period_covered: str,
    limit: int = 100
) -> List[FinancialChunk]:
    """Get financial chunks for a specific period (Q1 2025, FY 2024, etc.)"""
    return session.query(FinancialChunk)\
        .filter_by(period_covered=period_covered)\
        .order_by(FinancialChunk.created_at.desc())\
        .limit(limit)\
        .all()


def get_financial_by_company_and_period(
    session: Session,
    company_code: str,
    period_covered: str
) -> List[FinancialChunk]:
    """Get financial data for a company in a specific period"""
    return session.query(FinancialChunk)\
        .filter(
            FinancialChunk.company_code == company_code,
            FinancialChunk.period_covered == period_covered
        )\
        .order_by(FinancialChunk.metric_type.asc())\
        .all()


def get_pending_financial_embeddings(
    session: Session,
    limit: int = 100
) -> List[FinancialChunk]:
    """Get financial chunks pending embedding generation"""
    return session.query(FinancialChunk)\
        .filter_by(embedding_status="pending")\
        .order_by(FinancialChunk.created_at.asc())\
        .limit(limit)\
        .all()


# ============================================================================
# DIVIDEND QUERIES
# ============================================================================

def get_dividend_by_company(
    session: Session,
    company_code: str,
    limit: int = 100
) -> List[DividendChunk]:
    """Get dividend chunks for a company"""
    return session.query(DividendChunk)\
        .filter_by(company_code=company_code)\
        .order_by(DividendChunk.created_at.desc())\
        .limit(limit)\
        .all()


def get_dividend_by_type(
    session: Session,
    dividend_type: str,
    limit: int = 100
) -> List[DividendChunk]:
    """Get dividend chunks by type (interim, final, special)"""
    return session.query(DividendChunk)\
        .filter_by(dividend_type=dividend_type)\
        .order_by(DividendChunk.created_at.desc())\
        .limit(limit)\
        .all()


def get_upcoming_dividends(
    session: Session,
    from_date: str,
    to_date: str
) -> List[DividendChunk]:
    """Get dividend announcements with ex-dates in given range"""
    from datetime import datetime
    from_dt = datetime.strptime(from_date, "%Y-%m-%d").date()
    to_dt = datetime.strptime(to_date, "%Y-%m-%d").date()

    return session.query(DividendChunk)\
        .filter(
            DividendChunk.ex_date >= from_dt,
            DividendChunk.ex_date <= to_dt
        )\
        .order_by(DividendChunk.ex_date.asc())\
        .all()


def get_highest_dps(
    session: Session,
    limit: int = 10
) -> List[DividendChunk]:
    """Get highest dividend per share announcements"""
    return session.query(DividendChunk)\
        .order_by(DividendChunk.dps_value.desc())\
        .limit(limit)\
        .all()


def get_pending_dividend_embeddings(
    session: Session,
    limit: int = 100
) -> List[DividendChunk]:
    """Get dividend chunks pending embedding generation"""
    return session.query(DividendChunk)\
        .filter_by(embedding_status="pending")\
        .order_by(DividendChunk.created_at.asc())\
        .limit(limit)\
        .all()


# ============================================================================
# CORPORATE ACTION QUERIES
# ============================================================================

def get_corporate_action_by_company(
    session: Session,
    company_code: str,
    limit: int = 100
) -> List[CorporateActionChunk]:
    """Get corporate action chunks for a company"""
    return session.query(CorporateActionChunk)\
        .filter_by(company_code=company_code)\
        .order_by(CorporateActionChunk.created_at.desc())\
        .limit(limit)\
        .all()


def get_corporate_action_by_type(
    session: Session,
    action_type: str,
    limit: int = 100
) -> List[CorporateActionChunk]:
    """Get corporate actions by type (bonus, rights, split, consolidation)"""
    return session.query(CorporateActionChunk)\
        .filter_by(action_type=action_type)\
        .order_by(CorporateActionChunk.created_at.desc())\
        .limit(limit)\
        .all()


def get_upcoming_corporate_actions(
    session: Session,
    from_date: str,
    to_date: str
) -> List[CorporateActionChunk]:
    """Get corporate actions with effective dates in given range"""
    from datetime import datetime
    from_dt = datetime.strptime(from_date, "%Y-%m-%d").date()
    to_dt = datetime.strptime(to_date, "%Y-%m-%d").date()

    return session.query(CorporateActionChunk)\
        .filter(
            CorporateActionChunk.effective_date >= from_dt,
            CorporateActionChunk.effective_date <= to_dt
        )\
        .order_by(CorporateActionChunk.effective_date.asc())\
        .all()


def get_pending_corporate_action_embeddings(
    session: Session,
    limit: int = 100
) -> List[CorporateActionChunk]:
    """Get corporate action chunks pending embedding generation"""
    return session.query(CorporateActionChunk)\
        .filter_by(embedding_status="pending")\
        .order_by(CorporateActionChunk.created_at.asc())\
        .limit(limit)\
        .all()


# ============================================================================
# MEETING QUERIES
# ============================================================================

def get_meeting_by_company(
    session: Session,
    company_code: str,
    limit: int = 100
) -> List[MeetingChunk]:
    """Get meeting chunks for a company"""
    return session.query(MeetingChunk)\
        .filter_by(company_code=company_code)\
        .order_by(MeetingChunk.created_at.desc())\
        .limit(limit)\
        .all()


def get_meeting_by_type(
    session: Session,
    meeting_type: str,
    limit: int = 100
) -> List[MeetingChunk]:
    """Get meeting chunks by type (AGM, EGM, Special Meeting, etc.)"""
    return session.query(MeetingChunk)\
        .filter_by(meeting_type=meeting_type)\
        .order_by(MeetingChunk.created_at.desc())\
        .limit(limit)\
        .all()


def get_upcoming_meetings(
    session: Session,
    from_date: str,
    to_date: str
) -> List[MeetingChunk]:
    """Get meetings scheduled in given date range"""
    from datetime import datetime
    from_dt = datetime.strptime(from_date, "%Y-%m-%d").date()
    to_dt = datetime.strptime(to_date, "%Y-%m-%d").date()

    return session.query(MeetingChunk)\
        .filter(
            MeetingChunk.meeting_date >= from_dt,
            MeetingChunk.meeting_date <= to_dt
        )\
        .order_by(MeetingChunk.meeting_date.asc())\
        .all()


def get_pending_meeting_embeddings(
    session: Session,
    limit: int = 100
) -> List[MeetingChunk]:
    """Get meeting chunks pending embedding generation"""
    return session.query(MeetingChunk)\
        .filter_by(embedding_status="pending")\
        .order_by(MeetingChunk.created_at.asc())\
        .limit(limit)\
        .all()


# ============================================================================
# GENERIC/FALLBACK QUERIES
# ============================================================================

def get_pending_generic_embeddings(
    session: Session,
    limit: int = 100
) -> List[DocumentChunkVector]:
    """Get generic document chunks pending embedding generation"""
    return session.query(DocumentChunkVector)\
        .filter_by(embedding_status="pending")\
        .order_by(DocumentChunkVector.created_at.asc())\
        .limit(limit)\
        .all()


def get_all_pending_embeddings(
    session: Session,
    limit: int = 100
) -> Dict[str, int]:
    """Get count of pending embeddings across all categories"""
    counts = {
        "shareholding": session.query(ShareholdingChunk).filter_by(embedding_status="pending").count(),
        "financial": session.query(FinancialChunk).filter_by(embedding_status="pending").count(),
        "dividend": session.query(DividendChunk).filter_by(embedding_status="pending").count(),
        "corporate_action": session.query(CorporateActionChunk).filter_by(embedding_status="pending").count(),
        "meeting": session.query(MeetingChunk).filter_by(embedding_status="pending").count(),
        "generic": session.query(DocumentChunkVector).filter_by(embedding_status="pending").count(),
    }
    return counts


def get_embedding_stats(session: Session) -> Dict[str, Dict[str, int]]:
    """Get embedding statistics across all categories"""
    categories = {
        "shareholding": ShareholdingChunk,
        "financial": FinancialChunk,
        "dividend": DividendChunk,
        "corporate_action": CorporateActionChunk,
        "meeting": MeetingChunk,
        "generic": DocumentChunkVector,
    }

    stats = {}
    for category_name, model in categories.items():
        total = session.query(model).count()
        pending = session.query(model).filter_by(embedding_status="pending").count()
        stored = session.query(model).filter_by(embedding_status="stored").count()
        generated = session.query(model).filter_by(embedding_status="generated").count()

        stats[category_name] = {
            "total": total,
            "pending": pending,
            "stored": stored,
            "generated": generated,
        }

    return stats
