import { notFound } from 'next/navigation'
import { getCompany } from '@/lib/api/companies'
import { getCompanyFinancials, getFinancialTimeSeries } from '@/lib/api/financials'
import { MetricCard } from '@/components/data-display/metric-card'
import { ChartCard } from '@/components/data-display/chart-card'
import { FinancialChart } from '@/components/visualizations/financial-chart'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Download, FileText, Share2, TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

interface PageProps {
  params: Promise<{ code: string }>
}

export default async function FinancialsPage({ params }: PageProps) {
  const { code } = await params
  
  try {
    const company = await getCompany(code)
    const financials = await getCompanyFinancials(code)
    const timeSeriesData = await getFinancialTimeSeries(code)

    // Helper to find specific ratios
    const getRatio = (names: string[]) => 
      financials.find(r => names.some(n => r.ratio_name.includes(n)))

    const profitability = getRatio(['Return on Equity', 'Net Profit Margin', 'Net Interest Margin'])
    const liquidity = getRatio(['Current Ratio', 'Loan-to-Deposit', 'Liquidity'])
    const leverage = getRatio(['Debt-to-Equity', 'Capital Adequacy', 'Solvency'])

    // Prepare chart series
    const chartSeries = [
      { key: 'roe', name: 'ROE', color: '#06b6d4' }, // Cyan
      { key: 'roa', name: 'ROA', color: '#10b981' }, // Green
      { key: 'margin', name: 'Net Margin', color: '#f59e0b' } // Amber
    ]

    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-2xl font-bold text-text-primary tracking-tight">Financial Performance</h1>
            <p className="text-text-secondary mt-1">
              Financial health analysis and key performance indicators for {company.company_name}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" className="gap-2">
              <Download className="h-4 w-4" />
              Export Data
            </Button>
            <Button variant="outline" size="sm" className="gap-2">
              <FileText className="h-4 w-4" />
              Full Report
            </Button>
          </div>
        </div>

        {/* KPI Cards */}
        <div className="grid gap-4 md:grid-cols-3">
          {profitability && (
            <MetricCard
              label={profitability.ratio_name}
              value={`${profitability.ratio_value}%`}
              trend={{
                value: Math.abs(profitability.change_percent || 0),
                label: 'vs last quarter',
                direction: profitability.trend
              }}
              icon={profitability.trend === 'up' ? TrendingUp : (profitability.trend === 'down' ? TrendingDown : Minus)}
            />
          )}
          {liquidity && (
            <MetricCard
              label={liquidity.ratio_name}
              value={`${liquidity.ratio_value}${liquidity.ratio_name.includes('Ratio') && !liquidity.ratio_name.includes('%') ? '' : '%'}`}
              trend={{
                value: Math.abs(liquidity.change_percent || 0),
                label: 'vs last quarter',
                direction: liquidity.trend
              }}
              icon={liquidity.trend === 'up' ? TrendingUp : (liquidity.trend === 'down' ? TrendingDown : Minus)}
            />
          )}
          {leverage && (
            <MetricCard
              label={leverage.ratio_name}
              value={`${leverage.ratio_value}%`}
              trend={{
                value: Math.abs(leverage.change_percent || 0),
                label: 'vs last quarter',
                direction: leverage.trend
              }}
              icon={leverage.trend === 'up' ? TrendingUp : (leverage.trend === 'down' ? TrendingDown : Minus)}
            />
          )}
        </div>

        {/* Visualizations & Detail */}
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Main Chart */}
          <div className="lg:col-span-2">
            <ChartCard 
              title="Profitability & Efficiency Trends" 
              subtitle="Quarterly trend analysis of key profitability ratios"
              className="h-[400px]"
            >
              <FinancialChart 
                data={timeSeriesData} 
                series={chartSeries} 
                formatter={(val) => `${val}%`}
              />
            </ChartCard>
          </div>

          {/* Ratios List */}
          <Card className="bg-bg-card border-border-primary h-full">
            <CardHeader className="pb-2">
              <CardTitle className="text-base font-semibold">Key Ratios</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {financials.map((ratio, i) => (
                <div key={i} className="flex items-center justify-between pb-2 border-b border-border-secondary last:border-0 last:pb-0">
                  <div>
                    <p className="text-sm font-medium text-text-primary">{ratio.ratio_name}</p>
                    <p className="text-xs text-text-tertiary">{ratio.period}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-mono font-medium text-text-primary">
                      {ratio.ratio_value}%
                    </p>
                    <div className={`flex items-center justify-end text-xs ${
                      ratio.trend === 'up' ? 'text-success-primary' : 
                      ratio.trend === 'down' ? 'text-error-primary' : 'text-text-tertiary'
                    }`}>
                      {ratio.trend === 'up' ? <TrendingUp className="h-3 w-3 mr-1" /> : 
                       ratio.trend === 'down' ? <TrendingDown className="h-3 w-3 mr-1" /> : 
                       <Minus className="h-3 w-3 mr-1" />}
                      {Math.abs(ratio.change_percent || 0)}%
                    </div>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* Financial Statements Tabs */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-text-primary">Financial Statements</h2>
          <Tabs defaultValue="income" className="w-full">
            <TabsList className="bg-bg-secondary border border-border-secondary">
              <TabsTrigger value="income">Income Statement</TabsTrigger>
              <TabsTrigger value="balance">Balance Sheet</TabsTrigger>
              <TabsTrigger value="cashflow">Cash Flow</TabsTrigger>
            </TabsList>
            <div className="mt-4 border border-border-primary rounded-lg overflow-hidden bg-bg-card">
              <TabsContent value="income" className="m-0">
                <Table>
                  <TableHeader>
                    <TableRow className="hover:bg-transparent border-border-secondary">
                      <TableHead className="w-[300px]">Item</TableHead>
                      <TableHead className="text-right">2023</TableHead>
                      <TableHead className="text-right">2022</TableHead>
                      <TableHead className="text-right">2021</TableHead>
                      <TableHead className="text-right">Variance</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {[
                      { item: 'Revenue', y1: '12,450.5', y2: '11,200.0', y3: '10,800.0', var: '+11.2%' },
                      { item: 'Cost of Sales', y1: '(8,200.0)', y2: '(7,400.0)', y3: '(7,100.0)', var: '+10.8%' },
                      { item: 'Gross Profit', y1: '4,250.5', y2: '3,800.0', y3: '3,700.0', var: '+11.9%' },
                      { item: 'Operating Expenses', y1: '(1,850.0)', y2: '(1,750.0)', y3: '(1,700.0)', var: '+5.7%' },
                      { item: 'Operating Profit', y1: '2,400.5', y2: '2,050.0', y3: '2,000.0', var: '+17.1%' },
                      { item: 'Net Profit', y1: '1,850.5', y2: '1,550.0', y3: '1,500.0', var: '+19.4%' },
                    ].map((row, i) => (
                      <TableRow key={i} className="hover:bg-bg-elevated border-border-secondary/50">
                        <TableCell className="font-medium text-text-primary">{row.item}</TableCell>
                        <TableCell className="text-right font-mono text-text-secondary">{row.y1}</TableCell>
                        <TableCell className="text-right font-mono text-text-secondary">{row.y2}</TableCell>
                        <TableCell className="text-right font-mono text-text-secondary">{row.y3}</TableCell>
                        <TableCell className="text-right font-mono text-success-primary">{row.var}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TabsContent>
              <TabsContent value="balance" className="p-4 text-center text-text-tertiary italic m-0">
                Balance Sheet data would appear here properly formatted.
              </TabsContent>
              <TabsContent value="cashflow" className="p-4 text-center text-text-tertiary italic m-0">
                Cash Flow Statement data would appear here properly formatted.
              </TabsContent>
            </div>
          </Tabs>
        </div>
      </div>
    )
  } catch (error) {
    notFound()
  }
}
