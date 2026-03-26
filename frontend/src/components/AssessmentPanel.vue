<script setup lang="ts">
import { ref } from 'vue'
import { useParcelStore } from '@/stores/parcel'

const store = useParcelStore()
const showBreakdown = ref(false)

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
        <span
          class="score"
          @mouseenter="showBreakdown = true"
          @mouseleave="showBreakdown = false"
        >
          {{ Math.round(store.assessment.confidence_score * 100) }}% confidence &#9432;
          <div v-if="showBreakdown && store.assessment.confidence_breakdown" class="breakdown-tooltip">
            <div class="tooltip-header">Confidence Breakdown</div>
            <p class="tooltip-explain">
              The overall score is calculated from two independent checks:
              how complete the available data is, and how clearly the
              regulations apply.
            </p>

            <div class="bar-section">
              <div class="bar-label">
                <span>Data Quality</span>
                <span>{{ Math.round(store.assessment.confidence_breakdown.data_quality * 100) }}%</span>
              </div>
              <div class="bar-track">
                <div
                  class="bar-fill"
                  :style="{
                    width: Math.round(store.assessment.confidence_breakdown.data_quality * 100) + '%',
                    background: store.assessment.confidence_breakdown.data_quality >= 0.75 ? '#16a34a' : store.assessment.confidence_breakdown.data_quality >= 0.5 ? '#d97706' : '#dc2626'
                  }"
                ></div>
              </div>
              <div class="bar-hint">Is lot size, zone data, and building info available?</div>
            </div>

            <div class="bar-section">
              <div class="bar-label">
                <span>Rule Confidence</span>
                <span>{{ Math.round(store.assessment.confidence_breakdown.rule_confidence * 100) }}%</span>
              </div>
              <div class="bar-track">
                <div
                  class="bar-fill"
                  :style="{
                    width: Math.round(store.assessment.confidence_breakdown.rule_confidence * 100) + '%',
                    background: store.assessment.confidence_breakdown.rule_confidence >= 0.75 ? '#16a34a' : store.assessment.confidence_breakdown.rule_confidence >= 0.5 ? '#d97706' : '#dc2626'
                  }"
                ></div>
              </div>
              <div class="bar-hint">Are the zoning rules clearly stated or ambiguous?</div>
            </div>

            <div class="tooltip-divider"></div>

            <div class="bar-label overall-label">
              <span>Overall: Data Quality x Rule Confidence</span>
              <span>{{ Math.round(store.assessment.confidence_breakdown.overall * 100) }}%</span>
            </div>

            <div class="tooltip-divider"></div>

            <div class="tooltip-subheader">What affected this score</div>
            <ul class="factor-list">
              <li v-for="(f, i) in store.assessment.confidence_breakdown.factors" :key="i">{{ f }}</li>
            </ul>

            <div class="tooltip-divider"></div>

            <div class="grade-legend">
              <div class="grade-item"><span class="gl-badge" style="background:#16a34a">A</span> 90%+ &mdash; High confidence, complete data</div>
              <div class="grade-item"><span class="gl-badge" style="background:#2563eb">B</span> 75-89% &mdash; Mostly clear, minor gaps</div>
              <div class="grade-item"><span class="gl-badge" style="background:#d97706">C</span> 60-74% &mdash; Some data or rules missing</div>
              <div class="grade-item"><span class="gl-badge" style="background:#dc2626">D</span> &lt;60% &mdash; Significant gaps, verify with specialist</div>
            </div>
          </div>
        </span>
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

.score {
  color: #666;
  font-size: 13px;
  margin-left: auto;
  position: relative;
  cursor: help;
  text-decoration: underline dotted #999;
}

.breakdown-tooltip {
  position: absolute;
  top: 100%;
  right: 0;
  z-index: 100;
  background: #1a1a1a;
  color: #eee;
  border-radius: 10px;
  padding: 18px 20px;
  width: 360px;
  font-size: 13px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
  margin-top: 8px;
  line-height: 1.5;
}

.tooltip-header {
  font-size: 15px;
  font-weight: 700;
  margin-bottom: 6px;
  color: #fff;
}

.tooltip-explain {
  font-size: 12px;
  color: #999;
  margin-bottom: 14px;
}

.bar-section { margin-bottom: 12px; }

.bar-label {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 4px;
}

.bar-track {
  height: 8px;
  background: #333;
  border-radius: 4px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s ease;
}

.bar-hint {
  font-size: 11px;
  color: #777;
  margin-top: 2px;
}

.tooltip-divider {
  border-top: 1px solid #333;
  margin: 12px 0;
}

.overall-label {
  font-size: 14px;
  font-weight: 700;
  color: #fff;
}

.tooltip-subheader {
  font-size: 12px;
  font-weight: 600;
  color: #aaa;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 6px;
}

.factor-list {
  list-style: none;
  padding: 0;
}

.factor-list li {
  font-size: 12px;
  color: #bbb;
  padding: 2px 0 2px 12px;
  position: relative;
}

.factor-list li::before {
  content: '';
  position: absolute;
  left: 0;
  top: 9px;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #666;
}

.grade-legend {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.grade-item {
  font-size: 11px;
  color: #999;
  display: flex;
  align-items: center;
  gap: 6px;
}

.gl-badge {
  color: #fff;
  font-weight: 700;
  font-size: 10px;
  width: 18px;
  height: 18px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

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
