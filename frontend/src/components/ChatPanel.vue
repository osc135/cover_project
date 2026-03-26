<script setup lang="ts">
import { ref, computed } from 'vue'
import { useParcelStore } from '@/stores/parcel'
import { chat } from '@/services/api'

const store = useParcelStore()
const message = ref('')
const messages = ref<{ role: 'user' | 'assistant'; text: string }[]>([])
const loading = ref(false)

const suggestedQuestions = computed(() => {
  if (!store.assessment || !store.parcelData) return []
  const zone = store.parcelData.zoning.base_zone || 'this zone'
  const bt = store.assessment.building_type === 'SFH' ? 'single-family home'
    : store.assessment.building_type === 'ADU' ? 'ADU'
    : 'guest house'

  return [
    `What are the setback requirements for a ${bt} in ${zone}?`,
    `What is the maximum height allowed on this lot?`,
    `What is the floor area ratio (FAR) for ${zone}?`,
    `Can I build both a primary dwelling and an ADU on this lot?`,
  ]
})

async function send() {
  if (!message.value.trim() || !store.parcelData) return

  const text = message.value.trim()
  message.value = ''
  messages.value.push({ role: 'user', text })
  loading.value = true

  try {
    const reply = await chat(store.parcelData.parcel.apn, text)
    messages.value.push({ role: 'assistant', text: reply })
  } catch (e: any) {
    messages.value.push({ role: 'assistant', text: 'Sorry, something went wrong. Please try again.' })
  } finally {
    loading.value = false
  }
}

// Seed with open questions as suggestions
function askQuestion(q: string) {
  message.value = q
  send()
}
</script>

<template>
  <div class="chat-panel" v-if="store.assessment">
    <div class="chat-header">
      <h3>Ask a follow-up question</h3>
    </div>

    <!-- Suggested questions -->
    <div class="suggestions" v-if="messages.length === 0">
      <button
        v-for="(q, i) in suggestedQuestions"
        :key="i"
        class="suggestion-chip"
        @click="askQuestion(q)"
        :disabled="loading"
      >
        {{ q }}
      </button>
    </div>

    <!-- Messages -->
    <div class="messages" v-if="messages.length > 0">
      <div
        v-for="(msg, i) in messages"
        :key="i"
        :class="['message', msg.role]"
      >
        <div class="msg-label">{{ msg.role === 'user' ? 'You' : 'Assistant' }}</div>
        <div class="msg-text">{{ msg.text }}</div>
      </div>
      <div v-if="loading" class="message assistant">
        <div class="msg-label">Assistant</div>
        <div class="msg-text typing">Thinking...</div>
      </div>
    </div>

    <!-- Input -->
    <div class="chat-input">
      <input
        v-model="message"
        type="text"
        placeholder="Ask about zoning, setbacks, regulations..."
        @keyup.enter="send"
        :disabled="loading"
      />
      <button @click="send" :disabled="loading || !message.trim()">
        Send
      </button>
    </div>
  </div>
</template>

<style scoped>
.chat-panel {
  background: #fff;
  border: 1px solid #eee;
  border-radius: 12px;
  overflow: hidden;
}

.chat-header {
  padding: 16px 24px 0;
}

h3 {
  font-size: 13px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #999;
}

/* Suggestions */
.suggestions {
  padding: 12px 24px 16px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.suggestion-chip {
  text-align: left;
  padding: 10px 14px;
  border: 1px solid #eee;
  border-radius: 8px;
  background: #fafafa;
  font-size: 13px;
  color: #555;
  cursor: pointer;
  font-family: inherit;
  line-height: 1.4;
  transition: all 0.15s;
}

.suggestion-chip:hover:not(:disabled) {
  border-color: #1a1a1a;
  color: #1a1a1a;
}

.suggestion-chip:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Messages */
.messages {
  padding: 16px 24px;
  max-height: 400px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.msg-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #999;
}

.msg-text {
  font-size: 14px;
  line-height: 1.6;
  color: #333;
}

.message.user .msg-text {
  color: #1a1a1a;
  font-weight: 500;
}

.typing {
  color: #999;
  font-style: italic;
}

/* Input */
.chat-input {
  display: flex;
  gap: 0;
  border-top: 1px solid #eee;
}

.chat-input input {
  flex: 1;
  padding: 14px 20px;
  border: none;
  font-size: 14px;
  font-family: inherit;
  outline: none;
  background: #fafafa;
}

.chat-input input::placeholder {
  color: #bbb;
}

.chat-input button {
  padding: 14px 24px;
  background: #1a1a1a;
  color: #fff;
  border: none;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  font-family: inherit;
  transition: background 0.15s;
}

.chat-input button:hover:not(:disabled) {
  background: #333;
}

.chat-input button:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}
</style>
