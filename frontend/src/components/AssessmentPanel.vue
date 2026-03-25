<script setup lang="ts">
import { useParcelStore } from '@/stores/parcel'

const store = useParcelStore()

function gradeColor(grade: string) {
  switch (grade) {
    case 'A': return '#16a34a'
    case 'B': return '#2563eb'
    case 'C': return '#d97706'
    case 'D': return '#dc2626'
    default: return '#999'
  }
}

function confidenceColor(level: string) {
  switch (level) {
    case 'HIGH': return '#16a34a'
    case 'MEDIUM': return '#d97706'
    case 'LOW': return '#dc2626'
    default: return '#999'
  }
}
</script>

<template>
  <div class="assessment-panel" v-if="store.assessment">
    <!-- Summary -->
    <div class="summary-section">
      <div class="verdict-row">
        <span
          class="grade-badge"
          :style="{ background: gradeColor(store.assessment.confidence_grade) }"
        >
          {{ store.assessment.confidence_grade }}
        </span>
        <span class="buildable-tag" :class="store.assessment.buildable ? 'yes' : 'no'">
          {{ store.assessment.buildable ? 'Buildable' : 'Not Buildable' }}
        </span>
        <span class="score">{{ Math.round(store.assessment.confidence_score * 100) }}% confidence</span>
      </div>
      <p class="summary-text">{{ store.assessment.summary }}</p>
    </div>

    <!-- Constraints -->
    <div class="constraints-section">
      <h3>Constraints</h3>
      <table>
        <thead>
          <tr>
            <th>Rule</th>
            <th>Limit</th>
            <th>Applied</th>
            <th>Citation</th>
            <th>Confidence</th>
            <th>Type</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(c, i) in store.assessment.constraints" :key="i">
            <td>{{ c.rule }}</td>
            <td>{{ c.value }}</td>
            <td>{{ c.applied_to_parcel }}</td>
            <td class="citation">{{ c.citation }}</td>
            <td>
              <span class="confidence-tag" :style="{ color: confidenceColor(c.confidence) }">
                {{ c.confidence }}
              </span>
            </td>
            <td>
              <span :class="['type-tag', c.type]">{{ c.type }}</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Open Questions -->
    <div class="open-questions" v-if="store.assessment.open_questions.length > 0">
      <h3>Open Questions</h3>
      <ul>
        <li v-for="(q, i) in store.assessment.open_questions" :key="i">{{ q }}</li>
      </ul>
    </div>
  </div>

  <div class="assessment-panel empty" v-else-if="store.parcelData && !store.loading">
    <p>Select a building type above to run the assessment.</p>
  </div>
</template>

<style scoped>
.assessment-panel {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.assessment-panel.empty {
  padding: 24px;
  color: #888;
  text-align: center;
}

.summary-section {
  padding: 18px 20px;
  border-bottom: 1px solid #e0e0e0;
}

.verdict-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.grade-badge {
  color: #fff;
  font-weight: 700;
  font-size: 18px;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.buildable-tag {
  font-weight: 600;
  font-size: 14px;
  padding: 4px 10px;
  border-radius: 4px;
}
.buildable-tag.yes { background: #dcfce7; color: #16a34a; }
.buildable-tag.no { background: #fee2e2; color: #dc2626; }

.score { color: #666; font-size: 13px; margin-left: auto; }

.summary-text {
  font-size: 14px;
  line-height: 1.5;
  color: #333;
}

.constraints-section {
  padding: 16px 20px;
}

h3 {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 10px;
  color: #444;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

th {
  text-align: left;
  padding: 8px 10px;
  border-bottom: 2px solid #e0e0e0;
  font-weight: 600;
  color: #666;
  font-size: 12px;
  text-transform: uppercase;
}

td {
  padding: 8px 10px;
  border-bottom: 1px solid #f0f0f0;
}

.citation {
  font-family: monospace;
  font-size: 12px;
  color: #2563eb;
}

.confidence-tag { font-weight: 600; font-size: 12px; }

.type-tag {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 3px;
  background: #f0f0f0;
}
.type-tag.interpretive { background: #fef3c7; color: #92400e; }
.type-tag.deterministic { background: #dcfce7; color: #166534; }

.open-questions {
  padding: 16px 20px;
  border-top: 1px solid #e0e0e0;
  background: #fffbeb;
}

.open-questions ul {
  list-style: disc;
  padding-left: 20px;
}

.open-questions li {
  font-size: 13px;
  line-height: 1.5;
  color: #92400e;
  margin-bottom: 4px;
}
</style>
