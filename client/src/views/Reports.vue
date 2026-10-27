<template>
  <div class="reports">
    <div class="page-header">
      <h2>{{ t('reports.title') }}</h2>
      <p>{{ t('reports.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="monthlyRows.length === 0" class="card empty-state">{{ t('reports.noData') }}</div>
    <div v-else>
      <!-- Quarterly Performance -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('reports.quarterlyPerformance') }}</h3>
        </div>
        <div class="table-container">
          <table class="reports-table">
            <thead>
              <tr>
                <th>{{ t('reports.table.quarter') }}</th>
                <th>{{ t('reports.table.totalOrders') }}</th>
                <th>{{ t('reports.table.totalRevenue') }}</th>
                <th>{{ t('reports.table.avgOrderValue') }}</th>
                <th>{{ t('reports.table.fulfillmentRate') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="q in quarterlyData" :key="q.key">
                <td><strong>{{ formatQuarter(q) }}</strong></td>
                <td>{{ formatCount(q.totalOrders) }}</td>
                <td>{{ formatMoney(q.totalRevenue) }}</td>
                <td>{{ formatMoney(q.avgOrderValue) }}</td>
                <td>
                  <span :class="getFulfillmentClass(q.fulfillmentRate)">
                    {{ q.fulfillmentRate.toFixed(1) }}%
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Monthly Trends Chart -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('reports.monthlyRevenueTrend') }}</h3>
        </div>
        <div class="chart-container">
          <div class="bar-chart" role="img" :aria-label="t('reports.monthlyRevenueTrend')">
            <div v-for="bar in chartBars" :key="bar.month" class="bar-wrapper">
              <div class="bar-container">
                <div
                  class="bar"
                  :style="{ height: bar.height + 'px' }"
                  :title="bar.label + ': ' + formatMoney(bar.revenue)"
                ></div>
              </div>
              <div class="bar-label">{{ bar.label }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Month-over-Month Comparison -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('reports.monthOverMonth') }}</h3>
        </div>
        <div class="table-container">
          <table class="reports-table">
            <thead>
              <tr>
                <th>{{ t('reports.table.month') }}</th>
                <th>{{ t('reports.table.orders') }}</th>
                <th>{{ t('reports.table.revenue') }}</th>
                <th>{{ t('reports.table.change') }}</th>
                <th>{{ t('reports.table.growthRate') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in monthlyRows" :key="row.month">
                <td><strong>{{ formatMonth(row.month) }}</strong></td>
                <td>{{ formatCount(row.orderCount) }}</td>
                <td>{{ formatMoney(row.revenue) }}</td>
                <td>
                  <span v-if="row.change !== null" :class="getChangeClass(row.change)">
                    {{ formatChange(row.change) }}
                  </span>
                  <span v-else>-</span>
                </td>
                <td>
                  <span v-if="row.change !== null" :class="getChangeClass(row.change)">
                    {{ formatGrowthRate(row.growthRate) }}
                  </span>
                  <span v-else>-</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Summary Stats -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.stats.totalRevenue') }}</div>
          <div class="stat-value">{{ formatMoney(summary.totalRevenue) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.stats.avgMonthlyRevenue') }}</div>
          <div class="stat-value">{{ formatMoney(summary.avgMonthlyRevenue) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.stats.totalOrders') }}</div>
          <div class="stat-value">{{ formatCount(summary.totalOrders) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.stats.bestQuarter') }}</div>
          <div class="stat-value">{{ summary.bestQuarter ? formatQuarter(summary.bestQuarter) : '-' }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import { formatCurrency } from '../utils/currency'

const MAX_BAR_HEIGHT = 200

// Money is accumulated in integer cents so that summing many float totals
// (e.g. 87799.5 + ...) cannot produce noise like 5233075.9399999995.
const toCents = (amount) => Math.round((Number(amount) || 0) * 100)
const fromCents = (cents) => cents / 100

// Returns { year, month } (month 1-12) for a valid order date, otherwise null
const getOrderYearMonth = (dateString) => {
  if (!dateString) return null
  const date = new Date(dateString)
  if (isNaN(date.getTime())) return null
  return { year: date.getFullYear(), month: date.getMonth() + 1 }
}

export default {
  name: 'Reports',
  setup() {
    const { t, currentLocale, currentCurrency } = useI18n()
    const {
      selectedPeriod,
      selectedLocation,
      selectedCategory,
      selectedStatus,
      getCurrentFilters
    } = useFilters()

    const loading = ref(true)
    const error = ref(null)
    // Raw orders, already filtered server-side by month/warehouse/category/status.
    // The /api/reports/* endpoints ignore filters, so the report is derived from
    // the same filtered orders the Dashboard and Orders pages use.
    const allOrders = ref([])

    const loadData = async () => {
      try {
        loading.value = true
        error.value = null
        allOrders.value = await api.getOrders(getCurrentFilters())
      } catch (err) {
        error.value = t('reports.loadError')
        console.error('Failed to load reports:', err)
      } finally {
        loading.value = false
      }
    }

    // Monthly aggregates sorted chronologically (amounts in cents)
    const monthlyAggregates = computed(() => {
      const months = {}
      allOrders.value.forEach(order => {
        const ym = getOrderYearMonth(order.order_date)
        if (!ym) return
        const key = `${ym.year}-${String(ym.month).padStart(2, '0')}`
        if (!months[key]) {
          months[key] = { month: key, orderCount: 0, revenueCents: 0 }
        }
        months[key].orderCount++
        months[key].revenueCents += toCents(order.total_value)
      })
      return Object.values(months).sort((a, b) => a.month.localeCompare(b.month))
    })

    // Month rows with change vs. previous month precomputed (null for first row)
    const monthlyRows = computed(() => {
      return monthlyAggregates.value.map((m, index, list) => {
        const prev = index > 0 ? list[index - 1] : null
        const changeCents = prev ? m.revenueCents - prev.revenueCents : null
        return {
          month: m.month,
          orderCount: m.orderCount,
          revenue: fromCents(m.revenueCents),
          change: changeCents === null ? null : fromCents(changeCents),
          growthRate: prev && prev.revenueCents !== 0
            ? (changeCents / prev.revenueCents) * 100
            : null
        }
      })
    })

    const quarterlyData = computed(() => {
      const quarters = {}
      allOrders.value.forEach(order => {
        const ym = getOrderYearMonth(order.order_date)
        if (!ym) return
        const quarter = Math.ceil(ym.month / 3)
        const key = `${ym.year}-Q${quarter}`
        if (!quarters[key]) {
          quarters[key] = { key, year: ym.year, quarter, totalOrders: 0, revenueCents: 0, delivered: 0 }
        }
        quarters[key].totalOrders++
        quarters[key].revenueCents += toCents(order.total_value)
        if ((order.status || '').toLowerCase() === 'delivered') quarters[key].delivered++
      })
      return Object.values(quarters)
        .sort((a, b) => a.key.localeCompare(b.key))
        .map(q => ({
          key: q.key,
          year: q.year,
          quarter: q.quarter,
          totalOrders: q.totalOrders,
          totalRevenue: fromCents(q.revenueCents),
          avgOrderValue: fromCents(Math.round(q.revenueCents / q.totalOrders)),
          fulfillmentRate: (q.delivered / q.totalOrders) * 100
        }))
    })

    const chartBars = computed(() => {
      const maxRevenue = Math.max(0, ...monthlyRows.value.map(m => m.revenue))
      return monthlyRows.value.map(m => ({
        month: m.month,
        revenue: m.revenue,
        label: formatMonth(m.month),
        height: maxRevenue > 0 ? (m.revenue / maxRevenue) * MAX_BAR_HEIGHT : 0
      }))
    })

    const summary = computed(() => {
      const totalCents = monthlyAggregates.value.reduce((sum, m) => sum + m.revenueCents, 0)
      const monthCount = monthlyAggregates.value.length
      const totalOrders = monthlyAggregates.value.reduce((sum, m) => sum + m.orderCount, 0)
      const bestQuarter = quarterlyData.value.reduce(
        (best, q) => (!best || q.totalRevenue > best.totalRevenue ? q : best),
        null
      )
      return {
        totalRevenue: fromCents(totalCents),
        avgMonthlyRevenue: monthCount > 0 ? fromCents(Math.round(totalCents / monthCount)) : 0,
        totalOrders,
        bestQuarter
      }
    })

    const dateLocale = computed(() => (currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'))

    const formatMoney = (amount) => formatCurrency(amount, currentCurrency.value)

    const formatCount = (count) => Number(count || 0).toLocaleString(dateLocale.value)

    const formatMonth = (monthKey) => {
      const [year, month] = (monthKey || '').split('-').map(Number)
      const date = new Date(year, month - 1, 1)
      if (isNaN(date.getTime())) return monthKey
      return date.toLocaleDateString(dateLocale.value, { year: 'numeric', month: 'short' })
    }

    const formatQuarter = (q) => t('reports.quarterLabel', { quarter: q.quarter, year: q.year })

    const formatChange = (change) => {
      if (change > 0) return '+' + formatMoney(change)
      if (change < 0) return '-' + formatMoney(Math.abs(change))
      return formatMoney(0)
    }

    const formatGrowthRate = (rate) => {
      if (rate === null) return t('reports.notAvailable')
      return (rate > 0 ? '+' : '') + rate.toFixed(1) + '%'
    }

    const getFulfillmentClass = (rate) => {
      if (rate >= 90) return 'badge success'
      if (rate >= 75) return 'badge warning'
      return 'badge danger'
    }

    const getChangeClass = (change) => {
      if (change > 0) return 'positive-change'
      if (change < 0) return 'negative-change'
      return ''
    }

    // Reload whenever any global filter changes
    watch([selectedPeriod, selectedLocation, selectedCategory, selectedStatus], () => {
      loadData()
    })

    onMounted(loadData)

    return {
      t,
      loading,
      error,
      quarterlyData,
      monthlyRows,
      chartBars,
      summary,
      formatMoney,
      formatCount,
      formatMonth,
      formatQuarter,
      formatChange,
      formatGrowthRate,
      getFulfillmentClass,
      getChangeClass
    }
  }
}
</script>

<style scoped>
.reports {
  padding: 0;
}

.card {
  background: var(--surface);
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.card-header {
  margin-bottom: 1.5rem;
}

.card-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text);
  margin: 0;
}

.reports-table {
  width: 100%;
  border-collapse: collapse;
}

.reports-table th {
  background: var(--bg-subtle);
  padding: 0.75rem;
  text-align: left;
  font-weight: 600;
  color: var(--text-muted);
  border-bottom: 2px solid var(--border);
}

.reports-table td {
  padding: 0.75rem;
  border-bottom: 1px solid var(--border);
}

.reports-table tr:hover {
  background: var(--bg-subtle);
}

.chart-container {
  padding: 2rem 1rem;
  min-height: 300px;
}

.bar-chart {
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  height: 250px;
  gap: 0.5rem;
}

.bar-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  max-width: 80px;
}

.bar-container {
  height: 200px;
  display: flex;
  align-items: flex-end;
  width: 100%;
}

.bar {
  width: 100%;
  background: linear-gradient(to top, #3b82f6, #60a5fa);
  border-radius: 4px 4px 0 0;
  transition: all 0.3s;
  cursor: pointer;
}

.bar:hover {
  background: linear-gradient(to top, #2563eb, #3b82f6);
}

.bar-label {
  font-size: 0.75rem;
  color: var(--text-muted);
  text-align: center;
  transform: rotate(-45deg);
  white-space: nowrap;
  margin-top: 1.5rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
  margin-top: 1.5rem;
}

.stat-card {
  background: var(--surface);
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border-left: 4px solid #3b82f6;
}

.stat-label {
  font-size: 0.875rem;
  color: var(--text-muted);
  margin-bottom: 0.5rem;
}

.stat-value {
  font-size: 1.875rem;
  font-weight: 700;
  color: var(--text);
}

.badge {
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 500;
}

.badge.success {
  background: var(--success-bg-alt);
  color: var(--success-text-deep);
}

.badge.warning {
  background: var(--warning-bg-soft);
  color: var(--warning-text);
}

.badge.danger {
  background: var(--danger-bg);
  color: var(--danger-text);
}

.positive-change {
  color: #16a34a;
  font-weight: 600;
}

.negative-change {
  color: #dc2626;
  font-weight: 600;
}

.empty-state {
  text-align: center;
  color: var(--text-muted);
  padding: 3rem;
}

.loading {
  text-align: center;
  padding: 3rem;
  color: var(--text-muted);
}

.error {
  background: var(--danger-bg);
  color: var(--danger-text);
  padding: 1rem;
  border-radius: 8px;
  margin: 1rem 0;
}
</style>
