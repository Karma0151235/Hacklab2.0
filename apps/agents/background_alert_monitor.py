"""
Background Alert Monitoring Service
Continuously analyzes companies for financial risks and generates critical alerts
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional
import uuid

from agents.alert_agent import AlertAgent
from agents.rag_agent import RAGAgent
from agents.financial_agent import FinancialAgent
from agents.schemas import (
    RAGQuery,
    AlertAgentInput,
    Alert,
    AlertConfig,
    FinancialAgentInput,
)
from etl.logging_config import get_logger
from etl.db.models import GeneratedAlert, Company

logger = get_logger(__name__)


class BackgroundAlertMonitor:
    """
    Background service that:
    1. Fetches companies from database
    2. Analyzes each for financial risks
    3. Generates HIGH severity alerts
    4. Stores in database for frontend consumption
    """

    def __init__(self):
        """Initialize monitor with agents"""
        self.rag_agent = RAGAgent()
        self.financial_agent = FinancialAgent()
        self.alert_agent = AlertAgent()
        self.monitored_companies = []
        self.last_analysis_time = {}

    def get_companies_to_monitor(self) -> List[str]:
        """
        Get list of company codes to analyze.
        In production: fetch from database.
        For now: use hardcoded list of major Malaysian companies.
        """
        # TODO: Fetch from database
        # session = get_db_session()
        # return [c.company_code for c in session.query(Company).limit(50)]

        return [
            "1155",  # Malayan Banking
            "1082",  # Hong Leong Bank
            "1023",  # CIMB Group
            "6888",  # Axiata Group
            "4863",  # Tenaga Nasional
            "5347",  # Great Eastern
        ]

    def should_analyze(self, company_code: str, interval_hours: int = 24) -> bool:
        """
        Check if enough time has passed since last analysis
        Prevents analyzing the same company too frequently
        """
        last_time = self.last_analysis_time.get(company_code)
        if not last_time:
            return True

        time_since_last = datetime.utcnow() - last_time
        return time_since_last >= timedelta(hours=interval_hours)

    def analyze_company(self, company_code: str, company_name: str) -> List[Alert]:
        """
        Analyze a single company for financial risks

        Process:
        1. Query RAG for latest financial data
        2. Extract metrics via FinancialAgent
        3. Evaluate against thresholds via AlertAgent
        4. Return HIGH severity alerts only
        """
        try:
            logger.info(f"Starting background analysis for {company_name} ({company_code})")

            # Step 1: Retrieve financial documents
            query = f"Financial metrics and analysis for {company_name}"
            rag_output = self.rag_agent.retrieve(RAGQuery(query=query))

            if not rag_output or not rag_output.text_chunks:
                logger.warning(f"No financial data found for {company_code}")
                return []

            # Step 2: Extract financial metrics
            financial_input = FinancialAgentInput(
                query=query,
                context={"rag_output": rag_output.dict()},
            )
            financial_output = self.financial_agent.analyze(financial_input)

            if not financial_output or not financial_output.metrics:
                logger.warning(f"No metrics extracted for {company_code}")
                return []

            # Step 3: Evaluate alerts
            alert_input = AlertAgentInput(
                query=query,
                company_code=company_code,
                company_name=company_name,
                financial_metrics=financial_output.metrics,
                rag_output=rag_output,
                config=AlertConfig(),
            )

            alert_output = self.alert_agent.evaluate(alert_input)

            # Step 4: Filter HIGH severity alerts only
            critical_alerts = [a for a in alert_output.alerts if a.severity == "high"]

            logger.info(
                f"Analysis complete for {company_code}: {len(critical_alerts)} critical alerts"
            )
            return critical_alerts

        except Exception as e:
            logger.error(f"Error analyzing {company_code}: {str(e)}")
            return []

    def store_alerts(self, company_code: str, alerts: List[Alert]) -> int:
        """
        Store alerts in database and mark as needing notification

        Returns: Number of new alerts stored
        """
        # TODO: Implement database storage
        # In production: use SQLAlchemy session to insert GeneratedAlert records
        #
        # for alert in alerts:
        #     db_alert = GeneratedAlert(
        #         alert_id=str(uuid.uuid4()),
        #         company_code=company_code,
        #         company_name=alert.company_name,
        #         severity=alert.severity,
        #         alert_type=alert.alert_type,
        #         reason=alert.reason,
        #         metrics_data=alert_output.related_metrics,
        #         evidence=[e.dict() for e in alert.evidence],
        #         is_notified=False,
        #         status="active"
        #     )
        #     session.add(db_alert)
        # session.commit()

        logger.info(f"Stored {len(alerts)} critical alerts for {company_code}")
        return len(alerts)

    def run_analysis_cycle(self):
        """
        Single analysis cycle:
        1. Get list of companies
        2. Analyze each (respecting rate limits)
        3. Store critical alerts
        4. Update last analysis time
        """
        companies_to_analyze = self.get_companies_to_monitor()
        total_alerts = 0

        for company_code in companies_to_analyze:
            if not self.should_analyze(company_code):
                logger.debug(f"Skipping {company_code} - analyzed too recently")
                continue

            # Placeholder company name (would fetch from DB in production)
            company_name = company_code
            alerts = self.analyze_company(company_code, company_name)

            if alerts:
                stored_count = self.store_alerts(company_code, alerts)
                total_alerts += stored_count

            # Update tracking
            self.last_analysis_time[company_code] = datetime.utcnow()

        logger.info(f"Analysis cycle complete: {total_alerts} total critical alerts generated")

    def start_continuous_monitoring(self, interval_minutes: int = 60):
        """
        Start continuous background monitoring

        Args:
            interval_minutes: How often to run analysis cycle (default: 60 minutes)
        """
        logger.info(f"Starting background alert monitor (interval: {interval_minutes}m)")

        try:
            while True:
                self.run_analysis_cycle()
                # Sleep until next cycle
                sleep_seconds = interval_minutes * 60
                logger.info(f"Sleeping for {interval_minutes} minutes until next cycle")
                asyncio.sleep(sleep_seconds)
        except Exception as e:
            logger.error(f"Background monitor error: {str(e)}")
            raise


def start_background_monitoring():
    """
    Entry point to start background monitoring
    Call this from API startup
    """
    monitor = BackgroundAlertMonitor()
    # Run in background thread or use async scheduler
    # Example with APScheduler:
    # from apscheduler.schedulers.background import BackgroundScheduler
    # scheduler = BackgroundScheduler()
    # scheduler.add_job(monitor.run_analysis_cycle, 'interval', hours=1)
    # scheduler.start()
    logger.info("Background alert monitoring initialized")
    return monitor
