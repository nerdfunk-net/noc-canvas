<template>
  <div class="code-block-container">
    <div class="code-block-header">
      <div class="code-block-title">{{ title }}</div>
      <button
        @click="copyToClipboard"
        class="copy-button"
        :class="{ 'copied': copied }"
        title="Copy to clipboard"
      >
        <span v-if="!copied">📋 Copy</span>
        <span v-else>✓ Copied!</span>
      </button>
    </div>
    <div class="code-block-wrapper">
      <table class="code-table">
        <tbody>
          <tr
            v-for="(line, index) in highlightedLines"
            :key="index"
          >
            <td class="line-number">{{ index + 1 }}</td>
            <td class="code-line" v-html="line"></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

interface Props {
  code: string
  title?: string
  language?: 'cisco' | 'juniper' | 'plain'
}

const props = withDefaults(defineProps<Props>(), {
  title: 'Configuration',
  language: 'cisco'
})

const copied = ref(false)

const lines = computed(() => {
  return props.code.split('\n')
})

const lineCount = computed(() => lines.value.length)

// Simple syntax highlighting for network device configurations
const highlightLine = (line: string): string => {
  if (!line.trim()) return '&nbsp;'

  // Escape HTML first
  const escapedLine = line
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  if (props.language === 'cisco' || props.language === 'plain') {
    // Comments (lines starting with !)
    if (line.trim().startsWith('!')) {
      return `<span class="syntax-comment">${escapedLine}</span>`
    }

    // Check for special full-line patterns first
    if (/^interface\s+/i.test(line)) {
      return `<span class="syntax-interface">${escapedLine}</span>`
    }

    if (/^[A-Za-z0-9_-]+[#>]/.test(line)) {
      return `<span class="syntax-prompt">${escapedLine}</span>`
    }

    // Tokenize the line to avoid overlapping replacements
    const tokens: string[] = []
    let remaining = escapedLine

    // Split by spaces but keep track of what we're highlighting
    const words = remaining.split(/(\s+)/)

    for (let word of words) {
      if (!word) continue

      // Check if it's whitespace
      if (/^\s+$/.test(word)) {
        tokens.push(word)
        continue
      }

      let highlighted = word

      // Check for IP addresses (including subnet masks)
      if (/^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(\/\d{1,2})?$/.test(word)) {
        highlighted = `<span class="syntax-ip">${word}</span>`
      }
      // Check for keywords
      else if (/^(switchport|no|shutdown|enable|password|description|spanning-tree|channel-group|encapsulation|vrf|authentication|authorization|accounting|tacacs|radius|snmp-server|logging|ntp|clock|timezone|hostname|domain-name|service|permit|deny|access-group|crypto|key|trustpoint|certificate|secondary)$/i.test(word)) {
        highlighted = `<span class="syntax-keyword">${word}</span>`
      }
      // Check for configuration section keywords at start
      else if (/^(router|line|aaa|ip|ipv6|vlan|class-map|policy-map|service-policy|access-list)$/i.test(word) && tokens.length === 0) {
        highlighted = `<span class="syntax-section">${word}</span>`
      }
      // Check for quoted strings
      else if (/^".*"$/.test(word)) {
        highlighted = `<span class="syntax-string">${word}</span>`
      }

      tokens.push(highlighted)
    }

    return tokens.join('')
  }

  return escapedLine
}

const highlightedLines = computed(() => {
  return lines.value.map(line => highlightLine(line))
})

const copyToClipboard = async () => {
  try {
    await navigator.clipboard.writeText(props.code)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch (err) {
    console.error('Failed to copy:', err)
  }
}
</script>

<style scoped>
.code-block-container {
  background: #0d1117;
  border-radius: 8px;
  overflow: hidden;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

.code-block-header {
  background: #161b22;
  padding: 12px 16px;
  border-bottom: 1px solid #30363d;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.code-block-title {
  color: #c9d1d9;
  font-size: 14px;
  font-weight: 600;
}

.copy-button {
  background: #21262d;
  border: 1px solid #30363d;
  color: #c9d1d9;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
}

.copy-button:hover {
  background: #30363d;
  border-color: #8b949e;
}

.copy-button.copied {
  background: #238636;
  border-color: #238636;
  color: white;
}

.code-block-wrapper {
  max-height: 600px;
  overflow: auto;
  background: #0d1117;
}

.code-table {
  width: 100%;
  border-collapse: collapse;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
}

.code-table tbody tr {
  line-height: 1.5;
}

.line-number {
  background: #0d1117;
  padding: 0 16px;
  text-align: right;
  color: #6e7681;
  user-select: none;
  border-right: 1px solid #21262d;
  font-size: 12px;
  vertical-align: top;
  width: 1%;
  white-space: nowrap;
}

.code-line {
  padding: 0 16px;
  color: #c9d1d9;
  white-space: pre;
  vertical-align: top;
}

/* Syntax highlighting colors - GitHub dark theme inspired */
:deep(.syntax-comment) {
  color: #8b949e;
  font-style: italic;
}

:deep(.syntax-interface) {
  color: #79c0ff;
  font-weight: 600;
}

:deep(.syntax-section) {
  color: #d2a8ff;
  font-weight: 600;
}

:deep(.syntax-keyword) {
  color: #ff7b72;
}

:deep(.syntax-ip) {
  color: #a5d6ff;
}

:deep(.syntax-number) {
  color: #79c0ff;
}

:deep(.syntax-string) {
  color: #a5d6ff;
}

:deep(.syntax-prompt) {
  color: #7ee787;
  font-weight: 600;
}

/* Scrollbar styling */
.code-block-wrapper::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}

.code-block-wrapper::-webkit-scrollbar-track {
  background: #161b22;
}

.code-block-wrapper::-webkit-scrollbar-thumb {
  background: #30363d;
  border-radius: 5px;
}

.code-block-wrapper::-webkit-scrollbar-thumb:hover {
  background: #484f58;
}
</style>
