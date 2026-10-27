<template>
  <button
    type="button"
    class="theme-toggle"
    :aria-label="label"
    :title="label"
    :aria-pressed="theme === 'dark'"
    @click="toggleTheme"
  >
    <svg v-if="theme === 'dark'" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
      <path fill-rule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" clip-rule="evenodd" />
    </svg>
    <svg v-else xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
      <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" />
    </svg>
  </button>
</template>

<script>
import { computed } from 'vue'
import { useTheme } from '../composables/useTheme'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'ThemeToggle',
  setup() {
    const { theme, toggleTheme } = useTheme()
    const { t } = useI18n()

    // Label describes the action, so screen readers announce what pressing it will do
    const label = computed(() => t(theme.value === 'dark' ? 'theme.switchToLight' : 'theme.switchToDark'))

    return {
      theme,
      toggleTheme,
      label
    }
  }
}
</script>

<style scoped>
.theme-toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  margin-right: 1rem;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--surface);
  color: var(--text-muted);
  cursor: pointer;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}

.theme-toggle:hover {
  background: var(--surface-muted);
  color: var(--text);
  border-color: var(--border-strong);
}

.theme-toggle:focus-visible {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
}

.theme-toggle svg {
  width: 20px;
  height: 20px;
}
</style>
