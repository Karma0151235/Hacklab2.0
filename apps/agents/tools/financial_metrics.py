"""
Financial Metrics Calculator Tools
Deterministic, tool-based financial metric calculations
Never hallucinate values - only calculate from provided inputs
"""

from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from agents.schemas import FinancialMetrics
from etl.logging_config import get_logger

logger = get_logger(__name__)


class MetricStatus(str, Enum):
    """Status of metric calculation"""
    SUCCESS = "success"
    ERROR = "error"
    INSUFFICIENT_DATA = "insufficient_data"
    SKIPPED = "skipped"


@dataclass
class MetricResult:
    """Result of a metric calculation"""
    value: Optional[float] = None
    status: MetricStatus = MetricStatus.SUCCESS
    message: str = ""
    benchmark: Optional[float] = None
    interpretation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization"""
        return {
            "value": self.value,
            "status": self.status.value,
            "message": self.message,
            "benchmark": self.benchmark,
            "interpretation": self.interpretation
        }


class FinancialMetricsCalculator:
    """Tool-based financial metric calculations with comprehensive error handling"""

    # Industry benchmarks (Malaysia)
    BENCHMARKS = {
        'current_ratio': 1.5,
        'quick_ratio': 1.0,
        'debt_to_equity': 1.0,
        'debt_to_assets': 0.5,
        'interest_coverage': 3.0,
        'net_profit_margin': 0.10,
        'gross_profit_margin': 0.30,
        'operating_profit_margin': 0.15,
        'roa': 0.08,
        'roe': 0.15,
        'asset_turnover': 1.0,
        'inventory_turnover': 4.0,
        'receivables_turnover': 8.0,
    }

    @staticmethod
    def validate_inputs(**kwargs) -> Tuple[bool, Optional[str]]:
        """
        Validate inputs before calculation.

        Returns:
            Tuple of (is_valid, error_message)
        """
        for key, value in kwargs.items():
            if value is None:
                return False, f"Missing value for {key}"

            if not isinstance(value, (int, float)):
                return False, f"{key} must be numeric, got {type(value)}"

            if value < 0:
                return False, f"{key} must be non-negative, got {value}"

        return True, None

    # ======================== LIQUIDITY RATIOS ========================

    @staticmethod
    def current_ratio(current_assets: float, current_liabilities: float) -> MetricResult:
        """
        Calculate current ratio = Current Assets / Current Liabilities

        Interpretation:
        - >1.5: Good liquidity
        - 1.0-1.5: Acceptable
        - <1.0: Potential liquidity issues
        """
        is_valid, error = FinancialMetricsCalculator.validate_inputs(
            current_assets=current_assets,
            current_liabilities=current_liabilities
        )
        if not is_valid:
            return MetricResult(status=MetricStatus.ERROR, message=error)

        if current_liabilities == 0:
            return MetricResult(status=MetricStatus.ERROR, message="Current liabilities cannot be zero")

        ratio = current_assets / current_liabilities
        benchmark = FinancialMetricsCalculator.BENCHMARKS['current_ratio']

        interpretation = "Good" if ratio >= benchmark else "Below benchmark" if ratio < 1.0 else "Acceptable"

        return MetricResult(
            value=ratio,
            benchmark=benchmark,
            interpretation=interpretation,
            message=f"Company has RM{ratio:.2f} in current assets for every RM1 of current liabilities"
        )

    @staticmethod
    def quick_ratio(current_assets: float, inventory: float, current_liabilities: float) -> MetricResult:
        """
        Calculate quick ratio = (Current Assets - Inventory) / Current Liabilities

        More conservative than current ratio as it excludes inventory.
        """
        is_valid, error = FinancialMetricsCalculator.validate_inputs(
            current_assets=current_assets,
            inventory=inventory,
            current_liabilities=current_liabilities
        )
        if not is_valid:
            return MetricResult(status=MetricStatus.ERROR, message=error)

        if current_liabilities == 0:
            return MetricResult(status=MetricStatus.ERROR, message="Current liabilities cannot be zero")

        quick_assets = current_assets - inventory
        ratio = quick_assets / current_liabilities
        benchmark = FinancialMetricsCalculator.BENCHMARKS['quick_ratio']

        interpretation = "Good" if ratio >= benchmark else "Below benchmark" if ratio < 1.0 else "Acceptable"

        return MetricResult(
            value=ratio,
            benchmark=benchmark,
            interpretation=interpretation,
            message=f"Quick ratio of {ratio:.2f} (excluding inventory from liquid assets)"
        )

    # ======================== SOLVENCY RATIOS ========================

    @staticmethod
    def debt_to_equity(total_debt: float, equity: float) -> MetricResult:
        """
        Calculate debt-to-equity = Total Debt / Equity

        Interpretation:
        - <1.0: More equity than debt (lower risk)
        - 1.0-2.0: Moderate leverage
        - >2.0: High leverage (higher risk)
        """
        is_valid, error = FinancialMetricsCalculator.validate_inputs(
            total_debt=total_debt,
            equity=equity
        )
        if not is_valid:
            return MetricResult(status=MetricStatus.ERROR, message=error)

        if equity == 0:
            return MetricResult(status=MetricStatus.ERROR, message="Equity cannot be zero")

        ratio = total_debt / equity
        benchmark = FinancialMetricsCalculator.BENCHMARKS['debt_to_equity']

        interpretation = "Low leverage" if ratio < 1.0 else "Moderate leverage" if ratio <= 2.0 else "High leverage"

        return MetricResult(
            value=ratio,
            benchmark=benchmark,
            interpretation=interpretation,
            message=f"Company has RM{ratio:.2f} in debt for every RM1 of equity"
        )

    @staticmethod
    def debt_to_assets(total_debt: float, total_assets: float) -> MetricResult:
        """
        Calculate debt-to-assets = Total Debt / Total Assets

        Shows what portion of assets are financed by debt.
        """
        is_valid, error = FinancialMetricsCalculator.validate_inputs(
            total_debt=total_debt,
            total_assets=total_assets
        )
        if not is_valid:
            return MetricResult(status=MetricStatus.ERROR, message=error)

        if total_assets == 0:
            return MetricResult(status=MetricStatus.ERROR, message="Total assets cannot be zero")

        ratio = total_debt / total_assets
        benchmark = FinancialMetricsCalculator.BENCHMARKS['debt_to_assets']

        interpretation = "Conservative" if ratio < 0.5 else "Moderate" if ratio <= 0.7 else "Aggressive"

        return MetricResult(
            value=ratio * 100,  # Convert to percentage
            benchmark=benchmark * 100,
            interpretation=interpretation,
            message=f"{ratio*100:.1f}% of assets are financed by debt"
        )

    @staticmethod
    def equity_multiplier(total_assets: float, equity: float) -> MetricResult:
        """
        Calculate equity multiplier = Total Assets / Equity

        Higher multiplier indicates more leverage.
        """
        is_valid, error = FinancialMetricsCalculator.validate_inputs(
            total_assets=total_assets,
            equity=equity
        )
        if not is_valid:
            return MetricResult(status=MetricStatus.ERROR, message=error)

        if equity == 0:
            return MetricResult(status=MetricStatus.ERROR, message="Equity cannot be zero")

        multiplier = total_assets / equity

        return MetricResult(
            value=multiplier,
            interpretation="Higher leverage" if multiplier > 2.0 else "Moderate leverage",
            message=f"RM{multiplier:.2f} in assets per RM1 of equity"
        )

    @staticmethod
    def interest_coverage(operating_income: float, interest_expense: float) -> MetricResult:
        """
        Calculate interest coverage = Operating Income / Interest Expense

        How many times the company can cover interest payments from operations.

        Interpretation:
        - >3.0: Good coverage
        - 1.5-3.0: Acceptable
        - <1.5: High risk of not meeting obligations
        """
        is_valid, error = FinancialMetricsCalculator.validate_inputs(
            operating_income=operating_income,
            interest_expense=interest_expense
        )
        if not is_valid:
            return MetricResult(status=MetricStatus.ERROR, message=error)

        if interest_expense == 0:
            return MetricResult(status=MetricStatus.SUCCESS, value=float('inf'),
                              message="No interest expense - all debt is interest-free")

        ratio = operating_income / interest_expense
        benchmark = FinancialMetricsCalculator.BENCHMARKS['interest_coverage']

        interpretation = "Strong" if ratio >= benchmark else "Weak" if ratio < 1.5 else "Acceptable"

        return MetricResult(
            value=ratio,
            benchmark=benchmark,
            interpretation=interpretation,
            message=f"Operating income covers interest expense {ratio:.1f}x"
        )

    # ======================== PROFITABILITY RATIOS ========================

    @staticmethod
    def net_profit_margin(net_profit: float, revenue: float) -> MetricResult:
        """
        Calculate net profit margin = (Net Profit / Revenue) * 100

        Percentage of revenue that becomes profit.
        """
        is_valid, error = FinancialMetricsCalculator.validate_inputs(
            net_profit=net_profit,
            revenue=revenue
        )
        if not is_valid:
            return MetricResult(status=MetricStatus.ERROR, message=error)

        if revenue == 0:
            return MetricResult(status=MetricStatus.ERROR, message="Revenue cannot be zero")

        margin = (net_profit / revenue) * 100
        benchmark = FinancialMetricsCalculator.BENCHMARKS['net_profit_margin'] * 100

        interpretation = "Strong profitability" if margin >= benchmark else "Weak profitability" if margin < 0 else "Acceptable"

        return MetricResult(
            value=margin,
            benchmark=benchmark,
            interpretation=interpretation,
            message=f"Company retains {margin:.2f}% of revenue as net profit"
        )

    @staticmethod
    def gross_profit_margin(gross_profit: float, revenue: float) -> MetricResult:
        """
        Calculate gross profit margin = (Gross Profit / Revenue) * 100

        Profitability after cost of goods sold.
        """
        is_valid, error = FinancialMetricsCalculator.validate_inputs(
            gross_profit=gross_profit,
            revenue=revenue
        )
        if not is_valid:
            return MetricResult(status=MetricStatus.ERROR, message=error)

        if revenue == 0:
            return MetricResult(status=MetricStatus.ERROR, message="Revenue cannot be zero")

        margin = (gross_profit / revenue) * 100
        benchmark = FinancialMetricsCalculator.BENCHMARKS['gross_profit_margin'] * 100

        return MetricResult(
            value=margin,
            benchmark=benchmark,
            message=f"Gross profit margin: {margin:.2f}%"
        )

    @staticmethod
    def operating_profit_margin(operating_profit: float, revenue: float) -> MetricResult:
        """
        Calculate operating profit margin = (Operating Profit / Revenue) * 100

        Profitability from core operations.
        """
        is_valid, error = FinancialMetricsCalculator.validate_inputs(
            operating_profit=operating_profit,
            revenue=revenue
        )
        if not is_valid:
            return MetricResult(status=MetricStatus.ERROR, message=error)

        if revenue == 0:
            return MetricResult(status=MetricStatus.ERROR, message="Revenue cannot be zero")

        margin = (operating_profit / revenue) * 100
        benchmark = FinancialMetricsCalculator.BENCHMARKS['operating_profit_margin'] * 100

        return MetricResult(
            value=margin,
            benchmark=benchmark,
            message=f"Operating profit margin: {margin:.2f}%"
        )

    @staticmethod
    def return_on_assets(net_income: float, total_assets: float) -> MetricResult:
        """
        Calculate ROA = (Net Income / Total Assets) * 100

        How efficiently the company uses its assets.
        """
        is_valid, error = FinancialMetricsCalculator.validate_inputs(
            net_income=net_income,
            total_assets=total_assets
        )
        if not is_valid:
            return MetricResult(status=MetricStatus.ERROR, message=error)

        if total_assets == 0:
            return MetricResult(status=MetricStatus.ERROR, message="Total assets cannot be zero")

        roa = (net_income / total_assets) * 100
        benchmark = FinancialMetricsCalculator.BENCHMARKS['roa'] * 100

        interpretation = "Strong" if roa >= benchmark else "Weak" if roa < 0 else "Acceptable"

        return MetricResult(
            value=roa,
            benchmark=benchmark,
            interpretation=interpretation,
            message=f"Company generates {roa:.2f}% return on assets"
        )

    @staticmethod
    def return_on_equity(net_income: float, equity: float) -> MetricResult:
        """
        Calculate ROE = (Net Income / Equity) * 100

        Return generated for shareholders.
        """
        is_valid, error = FinancialMetricsCalculator.validate_inputs(
            net_income=net_income,
            equity=equity
        )
        if not is_valid:
            return MetricResult(status=MetricStatus.ERROR, message=error)

        if equity == 0:
            return MetricResult(status=MetricStatus.ERROR, message="Equity cannot be zero")

        roe = (net_income / equity) * 100
        benchmark = FinancialMetricsCalculator.BENCHMARKS['roe'] * 100

        interpretation = "Strong" if roe >= benchmark else "Weak" if roe < 0 else "Acceptable"

        return MetricResult(
            value=roe,
            benchmark=benchmark,
            interpretation=interpretation,
            message=f"Company generates {roe:.2f}% return on equity"
        )

    # ======================== EFFICIENCY RATIOS ========================

    @staticmethod
    def asset_turnover(revenue: float, total_assets: float) -> MetricResult:
        """
        Calculate asset turnover = Revenue / Total Assets

        How efficiently assets are used to generate revenue.
        """
        is_valid, error = FinancialMetricsCalculator.validate_inputs(
            revenue=revenue,
            total_assets=total_assets
        )
        if not is_valid:
            return MetricResult(status=MetricStatus.ERROR, message=error)

        if total_assets == 0:
            return MetricResult(status=MetricStatus.ERROR, message="Total assets cannot be zero")

        turnover = revenue / total_assets
        benchmark = FinancialMetricsCalculator.BENCHMARKS['asset_turnover']

        return MetricResult(
            value=turnover,
            benchmark=benchmark,
            message=f"Company generates RM{turnover:.2f} in revenue per RM1 of assets"
        )

    @staticmethod
    def inventory_turnover(cost_of_goods_sold: float, inventory: float) -> MetricResult:
        """
        Calculate inventory turnover = COGS / Inventory

        How many times inventory is sold and replaced.
        """
        is_valid, error = FinancialMetricsCalculator.validate_inputs(
            cost_of_goods_sold=cost_of_goods_sold,
            inventory=inventory
        )
        if not is_valid:
            return MetricResult(status=MetricStatus.ERROR, message=error)

        if inventory == 0:
            return MetricResult(status=MetricStatus.ERROR, message="Inventory cannot be zero")

        turnover = cost_of_goods_sold / inventory
        benchmark = FinancialMetricsCalculator.BENCHMARKS['inventory_turnover']

        days_in_inventory = 365 / turnover if turnover > 0 else 0

        return MetricResult(
            value=turnover,
            benchmark=benchmark,
            message=f"Inventory turns {turnover:.1f}x per year ({days_in_inventory:.0f} days to sell)"
        )

    @staticmethod
    def receivables_turnover(revenue: float, accounts_receivable: float) -> MetricResult:
        """
        Calculate receivables turnover = Revenue / Accounts Receivable

        How efficiently receivables are collected.
        """
        is_valid, error = FinancialMetricsCalculator.validate_inputs(
            revenue=revenue,
            accounts_receivable=accounts_receivable
        )
        if not is_valid:
            return MetricResult(status=MetricStatus.ERROR, message=error)

        if accounts_receivable == 0:
            return MetricResult(status=MetricStatus.ERROR, message="Accounts receivable cannot be zero")

        turnover = revenue / accounts_receivable
        benchmark = FinancialMetricsCalculator.BENCHMARKS['receivables_turnover']

        days_to_collect = 365 / turnover if turnover > 0 else 0

        return MetricResult(
            value=turnover,
            benchmark=benchmark,
            message=f"Receivables turn {turnover:.1f}x per year ({days_to_collect:.0f} days to collect)"
        )

    # ======================== GROWTH INDICATORS ========================

    @staticmethod
    def revenue_growth_yoy(current_revenue: float, previous_revenue: float) -> MetricResult:
        """
        Calculate YoY revenue growth = ((Current - Previous) / Previous) * 100
        """
        is_valid, error = FinancialMetricsCalculator.validate_inputs(
            current_revenue=current_revenue,
            previous_revenue=previous_revenue
        )
        if not is_valid:
            return MetricResult(status=MetricStatus.ERROR, message=error)

        if previous_revenue == 0:
            return MetricResult(status=MetricStatus.ERROR, message="Previous revenue cannot be zero")

        growth = ((current_revenue - previous_revenue) / previous_revenue) * 100

        interpretation = "Positive growth" if growth > 0 else "Declining" if growth < 0 else "Flat"

        return MetricResult(
            value=growth,
            interpretation=interpretation,
            message=f"Revenue grew {growth:.2f}% year-over-year"
        )

    @staticmethod
    def eps_growth(current_eps: float, previous_eps: float) -> MetricResult:
        """
        Calculate YoY EPS growth
        """
        is_valid, error = FinancialMetricsCalculator.validate_inputs(
            current_eps=current_eps,
            previous_eps=previous_eps
        )
        if not is_valid:
            return MetricResult(status=MetricStatus.ERROR, message=error)

        if previous_eps == 0:
            return MetricResult(status=MetricStatus.ERROR, message="Previous EPS cannot be zero")

        growth = ((current_eps - previous_eps) / previous_eps) * 100

        return MetricResult(
            value=growth,
            message=f"EPS grew {growth:.2f}% year-over-year"
        )

    @staticmethod
    def operating_income_growth(current_oi: float, previous_oi: float) -> MetricResult:
        """
        Calculate YoY operating income growth
        """
        is_valid, error = FinancialMetricsCalculator.validate_inputs(
            current_oi=current_oi,
            previous_oi=previous_oi
        )
        if not is_valid:
            return MetricResult(status=MetricStatus.ERROR, message=error)

        if previous_oi == 0:
            return MetricResult(status=MetricStatus.ERROR, message="Previous operating income cannot be zero")

        growth = ((current_oi - previous_oi) / previous_oi) * 100

        return MetricResult(
            value=growth,
            message=f"Operating income grew {growth:.2f}% year-over-year"
        )

    # ======================== PER-SHARE METRICS ========================

    @staticmethod
    def earnings_per_share(net_income: float, shares_outstanding: float) -> MetricResult:
        """
        Calculate EPS = Net Income / Shares Outstanding
        """
        is_valid, error = FinancialMetricsCalculator.validate_inputs(
            net_income=net_income,
            shares_outstanding=shares_outstanding
        )
        if not is_valid:
            return MetricResult(status=MetricStatus.ERROR, message=error)

        if shares_outstanding == 0:
            return MetricResult(status=MetricStatus.ERROR, message="Shares outstanding cannot be zero")

        eps = net_income / shares_outstanding

        return MetricResult(
            value=eps,
            message=f"Earnings per share: RM{eps:.4f}"
        )

    @staticmethod
    def book_value_per_share(equity: float, shares_outstanding: float) -> MetricResult:
        """
        Calculate BVPS = Equity / Shares Outstanding
        """
        is_valid, error = FinancialMetricsCalculator.validate_inputs(
            equity=equity,
            shares_outstanding=shares_outstanding
        )
        if not is_valid:
            return MetricResult(status=MetricStatus.ERROR, message=error)

        if shares_outstanding == 0:
            return MetricResult(status=MetricStatus.ERROR, message="Shares outstanding cannot be zero")

        bvps = equity / shares_outstanding

        return MetricResult(
            value=bvps,
            message=f"Book value per share: RM{bvps:.4f}"
        )

    # ======================== DUPONT ANALYSIS ========================

    @staticmethod
    def dupont_analysis(net_profit_margin_pct: float, asset_turnover: float, equity_multiplier: float) -> MetricResult:
        """
        Decompose ROE into components:
        ROE = Net Profit Margin × Asset Turnover × Equity Multiplier

        Shows how profitability, efficiency, and leverage combine to produce ROE.
        """
        roe = (net_profit_margin_pct / 100) * asset_turnover * equity_multiplier * 100

        interpretation = f"ROE of {roe:.2f}% is driven by: " \
                        f"Profitability ({net_profit_margin_pct:.2f}%), " \
                        f"Efficiency ({asset_turnover:.2f}x), " \
                        f"Leverage ({equity_multiplier:.2f}x)"

        return MetricResult(
            value=roe,
            interpretation=interpretation,
            message=interpretation
        )

    # ======================== BATCH CALCULATION ========================

    @staticmethod
    def calculate_all_available(financial_data: Dict[str, float]) -> Tuple[FinancialMetrics, Dict[str, MetricResult]]:
        """
        Calculate all metrics that can be computed from provided data.

        Returns:
            Tuple of (FinancialMetrics object, Dict of detailed results)
        """
        results = {}
        metrics_dict = {}

        # Attempt each metric calculation
        if all(k in financial_data for k in ['current_assets', 'current_liabilities']):
            result = FinancialMetricsCalculator.current_ratio(
                financial_data['current_assets'],
                financial_data['current_liabilities']
            )
            results['current_ratio'] = result
            if result.value is not None:
                metrics_dict['current_ratio'] = result.value

        if all(k in financial_data for k in ['current_assets', 'inventory', 'current_liabilities']):
            result = FinancialMetricsCalculator.quick_ratio(
                financial_data['current_assets'],
                financial_data['inventory'],
                financial_data['current_liabilities']
            )
            results['quick_ratio'] = result
            if result.value is not None:
                metrics_dict['quick_ratio'] = result.value

        if all(k in financial_data for k in ['total_debt', 'equity']):
            result = FinancialMetricsCalculator.debt_to_equity(
                financial_data['total_debt'],
                financial_data['equity']
            )
            results['debt_to_equity'] = result
            if result.value is not None:
                metrics_dict['debt_to_equity'] = result.value

        if all(k in financial_data for k in ['operating_income', 'interest_expense']):
            result = FinancialMetricsCalculator.interest_coverage(
                financial_data['operating_income'],
                financial_data['interest_expense']
            )
            results['interest_coverage'] = result
            if result.value is not None:
                metrics_dict['interest_coverage'] = result.value

        if all(k in financial_data for k in ['net_profit', 'revenue']):
            result = FinancialMetricsCalculator.net_profit_margin(
                financial_data['net_profit'],
                financial_data['revenue']
            )
            results['net_profit_margin'] = result
            if result.value is not None:
                metrics_dict['net_profit_margin'] = result.value

        if all(k in financial_data for k in ['net_income', 'total_assets']):
            result = FinancialMetricsCalculator.return_on_assets(
                financial_data['net_income'],
                financial_data['total_assets']
            )
            results['return_on_assets'] = result
            if result.value is not None:
                metrics_dict['return_on_assets'] = result.value

        if all(k in financial_data for k in ['net_income', 'equity']):
            result = FinancialMetricsCalculator.return_on_equity(
                financial_data['net_income'],
                financial_data['equity']
            )
            results['return_on_equity'] = result
            if result.value is not None:
                metrics_dict['return_on_equity'] = result.value

        if all(k in financial_data for k in ['revenue', 'total_assets']):
            result = FinancialMetricsCalculator.asset_turnover(
                financial_data['revenue'],
                financial_data['total_assets']
            )
            results['asset_turnover'] = result
            if result.value is not None:
                metrics_dict['asset_turnover'] = result.value

        # Profitability Margin Metrics
        if all(k in financial_data for k in ['gross_profit', 'revenue']):
            result = FinancialMetricsCalculator.gross_profit_margin(
                financial_data['gross_profit'],
                financial_data['revenue']
            )
            results['gross_profit_margin'] = result
            if result.value is not None:
                metrics_dict['gross_profit_margin'] = result.value

        if all(k in financial_data for k in ['operating_profit', 'revenue']):
            result = FinancialMetricsCalculator.operating_profit_margin(
                financial_data['operating_profit'],
                financial_data['revenue']
            )
            results['operating_profit_margin'] = result
            if result.value is not None:
                metrics_dict['operating_profit_margin'] = result.value

        # Growth Indicators
        if all(k in financial_data for k in ['revenue', 'previous_revenue']):
            result = FinancialMetricsCalculator.revenue_growth_yoy(
                financial_data['revenue'],
                financial_data['previous_revenue']
            )
            results['revenue_growth_yoy'] = result
            if result.value is not None:
                metrics_dict['revenue_growth_yoy'] = result.value

        if all(k in financial_data for k in ['earnings_per_share', 'previous_eps']):
            result = FinancialMetricsCalculator.eps_growth(
                financial_data['earnings_per_share'],
                financial_data['previous_eps']
            )
            results['eps_growth'] = result
            if result.value is not None:
                metrics_dict['eps_growth'] = result.value

        # Convert to FinancialMetrics schema
        metrics = FinancialMetrics(**metrics_dict)

        return metrics, results
