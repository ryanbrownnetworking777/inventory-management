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
          <div class="stat-value">{{ formatMoney(totalCost) }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.remainingBudget') }}</div>
          <div class="stat-value">{{ formatMoney(remainingBudget) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.itemCount') }}</div>
          <div class="stat-value">{{ items.length }}</div>
        </div>
      </div>

      <div v-if="error" class="error">{{ error }}</div>

      <div v-if="orderResult" class="success-message">
        <span>{{ t('restocking.orderSuccess', { orderNumber: orderResult.order_number }) }}</span>
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
                <td class="text-right"><strong>{{ item.quantity.toLocaleString() }}</strong></td>
                <td class="text-right">{{ formatUnitCost(item.unit_cost) }}</td>
                <td class="text-right"><strong>{{ formatMoney(item.subtotal) }}</strong></td>
                <td class="text-right">{{ t('restocking.leadTimeValue', { days: item.lead_time_days }) }}</td>
              </tr>
            </tbody>
          </table>
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

    let debounceTimer = null
    // Incremented per request so a slow, stale response can't overwrite a newer one
    let requestSeq = 0

    const items = computed(() => recommendation.value.items || [])
    const totalCost = computed(() => recommendation.value.total_cost || 0)
    // Based on the budget the server actually evaluated, so it stays consistent with totalCost while the slider moves
    const remainingBudget = computed(() => Math.max(0, (recommendation.value.budget || 0) - totalCost.value))

    // Round the slider max up to a whole step so the full candidate set remains reachable
    const sliderMax = computed(() => Math.ceil(maxBudget.value / BUDGET_STEP) * BUDGET_STEP)

    const canPlaceOrder = computed(() => items.value.length > 0 && !submitting.value && !recalculating.value)

    const formatMoney = (value) => formatCurrency(value || 0, currentCurrency.value)
    const formatUnitCost = (value) => formatCurrencyWithDecimals(value || 0, currentCurrency.value, 2)

    const loadRecommendations = async () => {
      const seq = ++requestSeq
      try {
        recalculating.value = true
        const data = await api.getRestockRecommendations(budget.value)
        if (seq !== requestSeq) return
        recommendation.value = data
        maxBudget.value = data.max_budget
        error.value = null
      } catch (err) {
        if (seq !== requestSeq) return
        error.value = `${t('restocking.loadError')}: ${err.message}`
        console.error('Failed to load restocking recommendations:', err)
      } finally {
        if (seq === requestSeq) recalculating.value = false
      }
    }

    const scheduleRecommendations = () => {
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
        // A zero budget returns no items but reports max_budget, which sizes the slider
        const probe = await api.getRestockRecommendations(0)
        maxBudget.value = probe.max_budget
        budget.value = Math.round((probe.max_budget * 0.5) / BUDGET_STEP) * BUDGET_STEP
        await loadRecommendations()
        initialized.value = !error.value
      } catch (err) {
        error.value = `${t('restocking.loadError')}: ${err.message}`
        console.error('Failed to initialize restocking:', err)
      } finally {
        loading.value = false
      }
    }

    const placeOrder = async () => {
      if (!canPlaceOrder.value) return
      try {
        submitting.value = true
        orderResult.value = null
        orderError.value = null
        const payload = {
          items: items.value.map(item => ({
            item_sku: item.item_sku,
            item_name: item.item_name,
            quantity: item.quantity,
            unit_cost: item.unit_cost,
            lead_time_days: item.lead_time_days
          }))
        }
        orderResult.value = await api.createRestockOrder(payload)
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
      submitting,
      orderResult,
      orderError,
      canPlaceOrder,
      formatMoney,
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
  color: #0f172a;
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
  color: #64748b;
}

.budget-hint {
  margin-top: 0.75rem;
  font-size: 0.875rem;
  color: #64748b;
}

.updating {
  margin-left: 0.5rem;
  font-size: 0.813rem;
  font-weight: 500;
  color: #64748b;
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
  background: #cbd5e1;
  border-color: #cbd5e1;
  cursor: not-allowed;
}

.success-message {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  color: #065f46;
  padding: 1rem;
  border-radius: 8px;
  margin: 1rem 0;
  font-size: 0.938rem;
}

.success-link {
  color: #047857;
  font-weight: 600;
  white-space: nowrap;
}

.success-link:hover {
  color: #065f46;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: #64748b;
  font-size: 0.938rem;
}

.demand-arrow {
  margin: 0 0.375rem;
  color: #94a3b8;
}

.text-right {
  text-align: right;
}
</style>
