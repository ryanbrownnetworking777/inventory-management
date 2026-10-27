import { ref } from 'vue'

const STORAGE_KEY = 'theme'

// Shared theme state (singleton): explicit user choice wins, otherwise follow the OS preference
const getInitialTheme = () => {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved === 'light' || saved === 'dark') return saved
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

const theme = ref(getInitialTheme())

const applyTheme = (value) => {
  document.documentElement.setAttribute('data-theme', value)
}

applyTheme(theme.value)

export function useTheme() {
  const setTheme = (value) => {
    theme.value = value
    localStorage.setItem(STORAGE_KEY, value)
    applyTheme(value)
  }

  const toggleTheme = () => {
    setTheme(theme.value === 'dark' ? 'light' : 'dark')
  }

  return {
    theme,
    setTheme,
    toggleTheme
  }
}
