<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen && backlogItem" class="modal-overlay" @click="close">
        <div class="modal-container" @click.stop>
          <div class="modal-header">
            <h3 class="modal-title">
              {{ mode === 'create' ? t('purchaseOrder.createTitle') : t('purchaseOrder.viewTitle') }}
            </h3>
            <button class="close-button" @click="close">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <!-- Backlog item context (shown in both modes) -->
            <div class="item-summary">
              <div class="item-summary-main">
                <h4 class="item-name">{{ translateProductName(backlogItem.item_name) }}</h4>
                <div class="item-meta">
                  <span class="mono">SKU: {{ backlogItem.item_sku }}</span>
                  <span class="mono">{{ t('purchaseOrder.orderId') }}: {{ backlogItem.order_id }}</span>
                </div>
              </div>
              <div class="shortage-pill">
                {{ t('purchaseOrder.shortage') }}: {{ shortage }} {{ t('purchaseOrder.units') }}
              </div>
            </div>

            <!-- Create mode -->
            <form v-if="mode === 'create'" class="po-form" novalidate @submit.prevent="submit">
              <div class="form-grid">
                <div class="form-field full">
                  <label for="po-supplier">{{ t('purchaseOrder.supplierName') }} <span class="required">*</span></label>
                  <input
                    id="po-supplier"
                    v-model="form.supplier_name"
                    type="text"
                    :class="{ invalid: fieldErrors.supplier_name }"
                    :placeholder="t('purchaseOrder.supplierPlaceholder')"
                    :disabled="submitting"
                  />
                  <div v-if="fieldErrors.supplier_name" class="field-error">{{ fieldErrors.supplier_name }}</div>
                </div>

                <div class="form-field">
                  <label for="po-quantity">{{ t('purchaseOrder.quantity') }} <span class="required">*</span></label>
                  <input
                    id="po-quantity"
                    v-model.number="form.quantity"
                    type="number"
                    min="1"
                    step="1"
                    :class="{ invalid: fieldErrors.quantity }"
                    :disabled="submitting"
                  />
                  <div v-if="fieldErrors.quantity" class="field-error">{{ fieldErrors.quantity }}</div>
                </div>

                <div class="form-field">
                  <label for="po-unit-cost">{{ t('purchaseOrder.unitCostUsd') }} <span class="required">*</span></label>
                  <input
                    id="po-unit-cost"
                    v-model.number="form.unit_cost"
                    type="number"
                    min="0.01"
                    step="0.01"
                    :class="{ invalid: fieldErrors.unit_cost }"
                    :disabled="submitting"
                  />
                  <div v-if="fieldErrors.unit_cost" class="field-error">{{ fieldErrors.unit_cost }}</div>
                </div>

                <div class="form-field full">
                  <label for="po-delivery">{{ t('purchaseOrder.expectedDelivery') }} <span class="required">*</span></label>
                  <input
                    id="po-delivery"
                    v-model="form.expected_delivery_date"
                    type="date"
                    :min="todayIso"
                    :class="{ invalid: fieldErrors.expected_delivery_date }"
                    :disabled="submitting"
                  />
                  <div v-if="fieldErrors.expected_delivery_date" class="field-error">{{ fieldErrors.expected_delivery_date }}</div>
                </div>

                <div class="form-field full">
                  <label for="po-notes">{{ t('purchaseOrder.notes') }}</label>
                  <textarea
                    id="po-notes"
                    v-model="form.notes"
                    rows="3"
                    :placeholder="t('purchaseOrder.notesPlaceholder')"
                    :disabled="submitting"
                  ></textarea>
                </div>
              </div>

              <div class="total-row">
                <span class="total-label">{{ t('purchaseOrder.totalCost') }}</span>
                <span class="total-value">{{ formattedFormTotal }}</span>
              </div>

              <div v-if="submitError" class="error-banner">{{ submitError }}</div>
            </form>

            <!-- View mode -->
            <div v-else>
              <div v-if="loading" class="state-message">{{ t('common.loading') }}</div>
              <div v-else-if="loadError" class="error-banner">{{ loadError }}</div>
              <div v-else-if="purchaseOrder" class="info-grid">
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.poId') }}</div>
                  <div class="info-value mono accent">{{ purchaseOrder.id }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.status') }}</div>
                  <div class="info-value">
                    <span class="badge" :class="statusClass(purchaseOrder.status)">
                      {{ translateStatus(purchaseOrder.status) }}
                    </span>
                  </div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.supplierName') }}</div>
                  <div class="info-value">{{ purchaseOrder.supplier_name }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.quantity') }}</div>
                  <div class="info-value">{{ purchaseOrder.quantity }} {{ t('purchaseOrder.units') }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.unitCost') }}</div>
                  <div class="info-value">{{ formatMoney(purchaseOrder.unit_cost) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.totalCost') }}</div>
                  <div class="info-value strong">{{ formatMoney(poTotal) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.expectedDelivery') }}</div>
                  <div class="info-value">{{ formatDate(purchaseOrder.expected_delivery_date) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.createdDate') }}</div>
                  <div class="info-value">{{ formatDate(purchaseOrder.created_date) }}</div>
                </div>
                <div class="info-item full">
                  <div class="info-label">{{ t('purchaseOrder.notes') }}</div>
                  <div class="info-value notes">{{ purchaseOrder.notes || t('purchaseOrder.noNotes') }}</div>
                </div>
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn-secondary" type="button" :disabled="submitting" @click="close">
              {{ mode === 'create' ? t('common.cancel') : t('common.close') }}
            </button>
            <button
              v-if="mode === 'create'"
              class="btn-primary"
              type="button"
              :disabled="submitting"
              @click="submit"
            >
              {{ submitting ? t('purchaseOrder.submitting') : t('purchaseOrder.submit') }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script>
import { ref, reactive, computed, watch } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrencyWithDecimals } from '../utils/currency'

// Build a YYYY-MM-DD string from the user's local date (toISOString would use UTC
// and can shift the day for users west/east of UTC).
const toLocalIsoDate = (date) => {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

export default {
  name: 'PurchaseOrderModal',
  props: {
    isOpen: {
      type: Boolean,
      default: false
    },
    backlogItem: {
      type: Object,
      default: null
    },
    mode: {
      type: String,
      default: 'create',
      validator: (value) => ['create', 'view'].includes(value)
    }
  },
  emits: ['close', 'po-created'],
  setup(props, { emit }) {
    const { t, currentLocale, currentCurrency, translateProductName } = useI18n()

    // Create-mode state
    const form = reactive({
      supplier_name: '',
      quantity: 1,
      unit_cost: null,
      expected_delivery_date: '',
      notes: ''
    })
    const fieldErrors = reactive({})
    const submitting = ref(false)
    const submitError = ref(null)

    // View-mode state
    const purchaseOrder = ref(null)
    const loading = ref(false)
    const loadError = ref(null)
    // Incremented on every (re)open/retarget so a late response for a previously opened
    // backlog item can't overwrite the PO shown for the item that is open now
    let loadSeq = 0

    const todayIso = computed(() => toLocalIsoDate(new Date()))

    const shortage = computed(() => {
      if (!props.backlogItem) return 0
      const diff = (props.backlogItem.quantity_needed || 0) - (props.backlogItem.quantity_available || 0)
      return Math.max(diff, 0)
    })

    const formTotal = computed(() => {
      const qty = Number(form.quantity)
      const cost = Number(form.unit_cost)
      if (!Number.isFinite(qty) || !Number.isFinite(cost)) return 0
      return qty * cost
    })

    const poTotal = computed(() => {
      if (!purchaseOrder.value) return 0
      return (Number(purchaseOrder.value.quantity) || 0) * (Number(purchaseOrder.value.unit_cost) || 0)
    })

    // Amounts are stored in USD; formatter converts to the selected display currency.
    const formatMoney = (amount) => formatCurrencyWithDecimals(Number(amount) || 0, currentCurrency.value, 2)

    const formattedFormTotal = computed(() => formatMoney(formTotal.value))

    const clearFieldErrors = () => {
      Object.keys(fieldErrors).forEach(key => delete fieldErrors[key])
    }

    const resetForm = () => {
      form.supplier_name = ''
      // Default to ordering exactly the shortage, but never less than 1 unit
      form.quantity = Math.max(shortage.value, 1)
      form.unit_cost = null
      form.expected_delivery_date = ''
      form.notes = ''
      clearFieldErrors()
      submitError.value = null
      submitting.value = false
    }

    const validate = () => {
      clearFieldErrors()

      if (!form.supplier_name || !form.supplier_name.trim()) {
        fieldErrors.supplier_name = t('purchaseOrder.errors.supplierRequired')
      }

      const qty = Number(form.quantity)
      if (form.quantity === '' || form.quantity === null || !Number.isInteger(qty) || qty < 1) {
        fieldErrors.quantity = t('purchaseOrder.errors.quantityInvalid')
      }

      const cost = Number(form.unit_cost)
      if (form.unit_cost === '' || form.unit_cost === null || !Number.isFinite(cost) || cost <= 0) {
        fieldErrors.unit_cost = t('purchaseOrder.errors.unitCostInvalid')
      }

      if (!form.expected_delivery_date) {
        fieldErrors.expected_delivery_date = t('purchaseOrder.errors.deliveryRequired')
      } else if (!/^\d{4}-\d{2}-\d{2}$/.test(form.expected_delivery_date)) {
        fieldErrors.expected_delivery_date = t('purchaseOrder.errors.deliveryInvalid')
      } else if (form.expected_delivery_date < todayIso.value) {
        // Lexical comparison is safe for zero-padded YYYY-MM-DD strings
        fieldErrors.expected_delivery_date = t('purchaseOrder.errors.deliveryPast')
      }

      return Object.keys(fieldErrors).length === 0
    }

    const extractApiError = (err) => {
      const detail = err?.response?.data?.detail
      if (typeof detail === 'string') return detail
      if (Array.isArray(detail) && detail.length > 0) {
        return detail.map(d => d.msg || JSON.stringify(d)).join('; ')
      }
      return err?.message || ''
    }

    const submit = async () => {
      if (submitting.value || !props.backlogItem) return
      submitError.value = null
      if (!validate()) return

      submitting.value = true
      try {
        const created = await api.createPurchaseOrder({
          backlog_item_id: props.backlogItem.id,
          supplier_name: form.supplier_name.trim(),
          quantity: Number(form.quantity),
          unit_cost: Number(form.unit_cost),
          expected_delivery_date: form.expected_delivery_date,
          notes: form.notes.trim() || null
        })
        emit('po-created', created)
      } catch (err) {
        console.error('Failed to create purchase order:', err)
        const detail = extractApiError(err)
        submitError.value = detail
          ? `${t('purchaseOrder.errors.createFailed')}: ${detail}`
          : t('purchaseOrder.errors.createFailed')
      } finally {
        submitting.value = false
      }
    }

    const loadPurchaseOrder = async () => {
      if (!props.backlogItem) return
      const seq = ++loadSeq
      // Reuse the PO already attached to the backlog item (e.g. right after creation)
      if (props.backlogItem.purchase_order) {
        purchaseOrder.value = props.backlogItem.purchase_order
        loadError.value = null
        loading.value = false
        return
      }

      try {
        loading.value = true
        loadError.value = null
        purchaseOrder.value = null
        const po = await api.getPurchaseOrderByBacklogItem(props.backlogItem.id)
        if (seq !== loadSeq) return
        purchaseOrder.value = po
      } catch (err) {
        if (seq !== loadSeq) return
        console.error('Failed to load purchase order:', err)
        loadError.value = err?.response?.status === 404
          ? t('purchaseOrder.errors.notFound')
          : t('purchaseOrder.errors.loadFailed')
      } finally {
        if (seq === loadSeq) loading.value = false
      }
    }

    // Re-initialise whenever the modal is opened (or retargeted while open)
    watch(
      () => [props.isOpen, props.backlogItem, props.mode],
      ([open]) => {
        if (!open || !props.backlogItem) {
          // Invalidate any in-flight view-mode request when the modal closes
          loadSeq++
          return
        }
        if (props.mode === 'create') loadSeq++
        if (props.mode === 'create') {
          resetForm()
        } else {
          loadPurchaseOrder()
        }
      },
      { immediate: true }
    )

    const close = () => {
      if (submitting.value) return
      emit('close')
    }

    const formatDate = (dateString) => {
      if (!dateString) return 'N/A'
      // Parse plain YYYY-MM-DD as a local date so it does not shift a day across timezones
      const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(dateString)
      const date = match
        ? new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]))
        : new Date(dateString)
      if (isNaN(date.getTime())) return dateString
      return date.toLocaleDateString(currentLocale.value === 'ja' ? 'ja-JP' : 'en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      })
    }

    const translateStatus = (status) => {
      if (!status) return 'N/A'
      const key = `purchaseOrder.statuses.${String(status).toLowerCase()}`
      const translated = t(key)
      // t() returns the key itself when no translation exists; fall back to the raw value
      return translated === key ? status : translated
    }

    const statusClass = (status) => {
      const map = {
        pending: 'warning',
        ordered: 'info',
        shipped: 'info',
        received: 'success',
        delivered: 'success',
        cancelled: 'danger'
      }
      return map[String(status || '').toLowerCase()] || 'info'
    }

    return {
      t,
      translateProductName,
      form,
      fieldErrors,
      submitting,
      submitError,
      purchaseOrder,
      loading,
      loadError,
      todayIso,
      shortage,
      poTotal,
      formattedFormTotal,
      formatMoney,
      formatDate,
      translateStatus,
      statusClass,
      submit,
      close
    }
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 1rem;
}

.modal-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.15);
  max-width: 640px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem;
  border-bottom: 1px solid #e2e8f0;
}

.modal-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.close-button {
  background: none;
  border: none;
  color: #64748b;
  cursor: pointer;
  padding: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: all 0.15s ease;
}

.close-button:hover {
  background: #f1f5f9;
  color: #0f172a;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem 2rem 2rem;
}

.item-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding-bottom: 1.25rem;
  margin-bottom: 1.5rem;
  border-bottom: 1px solid #e2e8f0;
}

.item-summary-main {
  min-width: 0;
}

.item-name {
  font-size: 1.125rem;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 0.375rem 0;
}

.item-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  font-size: 0.813rem;
  color: #64748b;
}

.mono {
  font-family: 'Monaco', 'Courier New', monospace;
}

.shortage-pill {
  flex-shrink: 0;
  padding: 0.375rem 0.75rem;
  border-radius: 6px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #dc2626;
  font-size: 0.813rem;
  font-weight: 600;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem 1.25rem;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.form-field.full {
  grid-column: 1 / -1;
}

.form-field label {
  font-size: 0.813rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.required {
  color: #ef4444;
}

.form-field input,
.form-field textarea {
  padding: 0.625rem 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.938rem;
  color: #0f172a;
  font-family: inherit;
  background: white;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.form-field textarea {
  resize: vertical;
}

.form-field input:focus,
.form-field textarea:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
}

.form-field input.invalid {
  border-color: #ef4444;
}

.form-field input:disabled,
.form-field textarea:disabled {
  background: #f8fafc;
  color: #64748b;
}

.field-error {
  font-size: 0.813rem;
  color: #dc2626;
}

.total-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 1.5rem;
  padding: 1rem 1.25rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
}

.total-label {
  font-size: 0.813rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.total-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
}

.error-banner {
  margin-top: 1rem;
  padding: 0.75rem 1rem;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #991b1b;
  font-size: 0.875rem;
}

.state-message {
  padding: 2rem;
  text-align: center;
  color: #64748b;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.info-item.full {
  grid-column: 1 / -1;
}

.info-label {
  font-size: 0.813rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.info-value {
  font-size: 0.938rem;
  color: #0f172a;
  font-weight: 500;
}

.info-value.accent {
  color: #2563eb;
}

.info-value.strong {
  font-weight: 700;
}

.info-value.notes {
  white-space: pre-wrap;
  color: #334155;
}

.badge {
  display: inline-block;
  padding: 0.25rem 0.625rem;
  border-radius: 6px;
  font-size: 0.813rem;
  font-weight: 600;
}

.badge.success {
  background: #d1fae5;
  color: #065f46;
}

.badge.info {
  background: #dbeafe;
  color: #1e40af;
}

.badge.warning {
  background: #fef3c7;
  color: #92400e;
}

.badge.danger {
  background: #fecaca;
  color: #991b1b;
}

.modal-footer {
  padding: 1.5rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.btn-secondary,
.btn-primary {
  padding: 0.625rem 1.25rem;
  border-radius: 8px;
  font-weight: 500;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-secondary {
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  color: #334155;
}

.btn-secondary:hover:not(:disabled) {
  background: #e2e8f0;
  border-color: #cbd5e1;
}

.btn-primary {
  background: #0f172a;
  border: 1px solid #0f172a;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #1e293b;
}

.btn-primary:disabled,
.btn-secondary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@media (max-width: 600px) {
  .form-grid,
  .info-grid {
    grid-template-columns: 1fr;
  }
}

/* Modal transition animations */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: transform 0.2s ease;
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.95);
}
</style>
