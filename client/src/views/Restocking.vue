<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error && !initialized" class="error">{{ error }}</div>
    <div v-else>
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.budgetLabel') }}</h3>
          <span class="budget-display">{{ formatMoney(budget) }}</span>
        </div>
        <input
          v-model.number="budget"
          type="range"
          class="budget-slider"
          min="0"
          :max="sliderMax"
          :step="BUDGET_STEP"
          :disabled="sliderMax === 0"
          :aria-label="t('restocking.budgetLabel')"
          @input="scheduleRecommendations"
        />
        <div class="budget-scale">
          <span>{{ formatMoney(0) }}</span>
          <span>{{ formatMoney(sliderMax) }}</span>
        </div>
        <p class="budget-hint">{{ t('restocking.budgetHint') }}</p>
      </div>

      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.budget') }}</div>
          <div class="stat-value">{{ formatMoney(budget) }}</div>
        </div>
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.recommendedTotal') }}</div>
          <div class="stat-value">{{ formatMoneyExact(totalCost) }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.remainingBudget') }}</div>
          <div class="stat-value">{{ formatMoneyExact(remainingBudget) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.itemCount') }}</div>
          <div class="stat-value">{{ items.length }}</div>
        </div>
      </div>

      <div v-if="error" class="error">{{ error }}</div>

      <div v-if="orderResult" class="success-message">
        <span>
          {{ t('restocking.orderSuccess', { orderNumber: orderResult.order_number }) }}
          {{ t('restocking.orderPlacedHint') }}
        </span>
        <router-link to="/orders" class="success-link">{{ t('restocking.viewOrders') }}</router-link>
      </div>
      <div v-if="orderError" class="error">{{ orderError }}</div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">
            {{ t('restocking.recommendations') }} ({{ items.length }})
            <span v-if="recalculating" class="updating">{{ t('restocking.updating') }}</span>
          </h3>
          <button
            type="button"
            class="btn-primary"
            :disabled="!canPlaceOrder"
            @click="placeOrder"
          >
            {{ submitting ? t('restocking.submitting') : t('restocking.placeOrder') }}
          </button>
        </div>

        <div v-if="items.length === 0" class="empty-state">
          {{ maxBudget === 0 ? t('restocking.noCandidates') : t('restocking.noItems') }}
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.itemName') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th>{{ t('restocking.table.demand') }}</th>
                <th class="text-right">{{ t('restocking.table.quantity') }}</th>
                <th class="text-right">{{ t('restocking.table.unitCost') }}</th>
                <th class="text-right">{{ t('restocking.table.subtotal') }}</th>
                <th class="text-right">{{ t('restocking.table.leadTime') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in items" :key="item.item_sku">
                <td><strong>{{ item.item_sku }}</strong></td>
                <td>{{ translateProductName(item.item_name) }}</td>
                <td>
                  <span :class="['badge', item.trend]">{{ t(`trends.${item.trend}`) }}</span>
                </td>
                <td>
                  {{ item.current_demand.toLocaleString() }}
                  <span class="demand-arrow">→</span>
                  <strong>{{ item.forecasted_demand.toLocaleString() }}</strong>
                </td>
                <td class="text-right">
                  <span v-if="item.partial" class="badge warning partial-badge">{{ t('restocking.partial') }}</span>
                  <strong>{{ item.quantity.toLocaleString() }}</strong>
                  <span v-if="item.partial" class="qty-recommended"> / {{ item.recommended_quantity.toLocaleString() }}</span>
                </td>
                <td class="text-right">{{ formatUnitCost(item.unit_cost) }}</td>
                <td class="text-right"><strong>{{ formatMoneyExact(item.subtotal) }}</strong></td>
                <td class="text-right">{{ t('restocking.leadTimeValue', { days: item.lead_time_days }) }}</td>
              </tr>
            </tbody>
          </table>
          <p v-if="hasPartial" class="partial-note">{{ t('restocking.partialNote') }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrency, formatCurrencyWithDecimals } from '../utils/currency'

const BUDGET_STEP = 50
const DEBOUNCE_MS = 250

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, translateProductName } = useI18n()

    const loading = ref(true)
    const initialized = ref(false)
    const recalculating = ref(false)
    const error = ref(null)

    const budget = ref(0)
    const maxBudget = ref(0)
    const recommendation = ref({ items: [], total_cost: 0, budget: 0 })

    const submitting = ref(false)
    const orderResult = ref(null)
    const orderError = ref(null)

    // True from the moment the slider moves until the response for the CURRENT budget arrives,
    // so the user can never order a list computed for a previous budget
    const stale = ref(false)
    // Set after a successful order; cleared only when the budget changes, preventing duplicate orders
    const orderPlaced = ref(false)

    let debounceTimer = null
    // Incremented per request so a slow, stale response can't overwrite a newer one
    let requestSeq = 0

    const items = computed(() => recommendation.value.items || [])
    const totalCost = computed(() => recommendation.value.total_cost || 0)
    // Based on the budget the server actually evaluated, so it stays consistent with totalCost while the slider moves
    const remainingBudget = computed(() => Math.max(0, (recommendation.value.budget || 0) - totalCost.value))

    // Round the slider max up to a whole step so the full candidate set remains reachable
    const sliderMax = computed(() => Math.ceil(maxBudget.value / BUDGET_STEP) * BUDGET_STEP)

    const hasPartial = computed(() => items.value.some(item => item.partial))

    const canPlaceOrder = computed(() =>
      items.value.length > 0 &&
      !submitting.value &&
      !recalculating.value &&
      !stale.value &&
      !orderPlaced.value
    )

    const formatMoney = (value) => formatCurrency(value || 0, currentCurrency.value)
    // Subtotals/totals are exact to the cent, so show 2 decimals (JPY shows whole yen)
    const formatMoneyExact = (value) => formatCurrencyWithDecimals(value || 0, currentCurrency.value, 2)
    const formatUnitCost = formatMoneyExact

    const loadRecommendations = async () => {
      const seq = ++requestSeq
      try {
        recalculating.value = true
        const data = await api.getRestockRecommendations(budget.value)
        if (seq !== requestSeq) return
        recommendation.value = data
        maxBudget.value = data.max_budget
        error.value = null
        // Only the latest request (matching the current slider value) clears the stale flag
        stale.value = false
      } catch (err) {
        if (seq !== requestSeq) return
        error.value = `${t('restocking.loadError')}: ${err.message}`
        console.error('Failed to load restocking recommendations:', err)
      } finally {
        if (seq === requestSeq) recalculating.value = false
      }
    }

    const scheduleRecommendations = () => {
      // Disable ordering immediately (before the debounce fires) until fresh results arrive
      stale.value = true
      orderPlaced.value = false
      // A previous order confirmation no longer matches the list once the budget changes
      orderResult.value = null
      orderError.value = null
      clearTimeout(debounceTimer)
      debounceTimer = setTimeout(loadRecommendations, DEBOUNCE_MS)
    }

    const initialize = async () => {
      try {
        loading.value = true
        error.value = null
        // Omitting the budget lets the server choose a default; it echoes that value back in `budget`
        const seq = ++requestSeq
        const data = await api.getRestockRecommendations()
        if (seq !== requestSeq) return
        recommendation.value = data
        maxBudget.value = data.max_budget
        budget.value = data.budget
        stale.value = false
        initialized.value = true
      } catch (err) {
        error.value = `${t('restocking.loadError')}: ${err.message}`
        console.error('Failed to initialize restocking:', err)
      } finally {
        loading.value = false
      }
    }

    const placeOrder = async () => {
      // canPlaceOrder includes !submitting, and submitting is set synchronously below, so double-clicks are ignored
      if (!canPlaceOrder.value) return
      try {
        submitting.value = true
        orderResult.value = null
        orderError.value = null
        const payload = {
          // Server looks up name, unit cost, and lead time itself
          items: items.value.map(item => ({
            item_sku: item.item_sku,
            quantity: item.quantity
          }))
        }
        orderResult.value = await api.createRestockOrder(payload)
        orderPlaced.value = true
      } catch (err) {
        orderError.value = t('restocking.orderError')
        console.error('Failed to place restock order:', err)
      } finally {
        submitting.value = false
      }
    }

    onMounted(initialize)

    onBeforeUnmount(() => {
      clearTimeout(debounceTimer)
    })

    return {
      t,
      BUDGET_STEP,
      loading,
      initialized,
      recalculating,
      error,
      budget,
      maxBudget,
      sliderMax,
      items,
      totalCost,
      remainingBudget,
      hasPartial,
      submitting,
      orderResult,
      orderError,
      canPlaceOrder,
      formatMoney,
      formatMoneyExact,
      formatUnitCost,
      scheduleRecommendations,
      placeOrder,
      translateProductName
    }
  }
}
</script>

<style scoped>
.budget-display {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text);
  letter-spacing: -0.025em;
}

.budget-slider {
  width: 100%;
  accent-color: #2563eb;
  cursor: pointer;
}

.budget-slider:disabled {
  cursor: not-allowed;
}

.budget-scale {
  display: flex;
  justify-content: space-between;
  margin-top: 0.25rem;
  font-size: 0.813rem;
  color: var(--text-muted);
}

.budget-hint {
  margin-top: 0.75rem;
  font-size: 0.875rem;
  color: var(--text-muted);
}

.updating {
  margin-left: 0.5rem;
  font-size: 0.813rem;
  font-weight: 500;
  color: var(--text-muted);
}

.btn-primary {
  padding: 0.625rem 1.25rem;
  background: #2563eb;
  border: 1px solid #2563eb;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.875rem;
  color: white;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
  border-color: #1d4ed8;
}

.btn-primary:disabled {
  background: var(--border-strong);
  border-color: var(--border-strong);
  cursor: not-allowed;
}

.success-message {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  background: var(--success-bg-subtle);
  border: 1px solid var(--success-border);
  color: var(--success-text);
  padding: 1rem;
  border-radius: 8px;
  margin: 1rem 0;
  font-size: 0.938rem;
}

.success-link {
  color: var(--success-text-alt);
  font-weight: 600;
  white-space: nowrap;
}

.success-link:hover {
  color: var(--success-text);
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: var(--text-muted);
  font-size: 0.938rem;
}

.demand-arrow {
  margin: 0 0.375rem;
  color: var(--text-faint);
}

.text-right {
  text-align: right;
}

.partial-badge {
  margin-right: 0.5rem;
  padding: 0.125rem 0.5rem;
  font-size: 0.688rem;
}

.qty-recommended {
  color: var(--text-muted);
}

.partial-note {
  margin-top: 0.75rem;
  font-size: 0.813rem;
  color: var(--text-muted);
}
</style>
