<script setup lang="ts">
import { ref } from 'vue'
import { useParcelStore } from '@/stores/parcel'

const store = useParcelStore()
const showBreakdown = ref(false)

function gradeColor(grade: string) {
  switch (grade) {
    case 'A': return '#16a34a'
    case 'B': return '#1a1a1a'
    case 'C': return '#92400e'
    case 'D': return '#dc2626'
    default: return '#999'
  }
}

function confidenceColor(level: string) {
  switch (level) {
    case 'HIGH': return '#16a34a'
    case 'MEDIUM': return '#92400e'
    case 'LOW': return '#dc2626'
    default: return '#999'
  }
}

function barColor(val: number) {
  if (val >= 0.75) return '#16a34a'
  if (val >= 0.5) return '#92400e'
  return '#dc2626'
}
</script>

<template>
  <div class="assessment-panel" v-if="store.assessment">
    <!-- Verdict -->
    <div class="verdict-section">
      <div class="verdict-top">
        <span
          class="grade-badge"
          :style="{ background: gradeColor(store.assessment.confidence_grade) }"
        >
          {{ store.assessment.confidence_grade }}
        </span>
        <div class="verdict-text">
          <span class="buildable-label" :class="store.assessment.buildable ? 'yes' : 'no'">
            {{ store.assessment.buildable ? 'Buildable' : 'Not Buildable' }}
          </span>
          <span
            class="confidence-score"
            @mouseenter="showBreakdown = true"
            @mouseleave="showBreakdown = false"
          >
            {{ Math.round(store.assessment.confidence_score * 100) }}% confidence &#9432;

            <!-- Tooltip -->
            <div v-if="showBreakdown && store.assessment.confidence_breakdown" class="tooltip">
              <div class="tooltip-title">Confidence Breakdown</div>
              <p class="tooltip-desc">
                Score is calculated from two independent checks: data completeness and regulatory clarity.
              </p>

              <div class="bar-group">
                <div class="bar-row">
                  <span>Data Quality</span>
                  <span>{{ Math.round(store.assessment.confidence_breakdown.data_quality * 100) }}%</span>
                </div>
                <div class="bar-track">
                  <div class="bar-fill" :style="{ width: (store.assessment.confidence_breakdown.data_quality * 100) + '%', background: barColor(store.assessment.confidence_breakdown.data_quality) }"></div>
                </div>
                <div class="bar-hint">Lot size, zone data, building info available?</div>
              </div>

              <div class="bar-group">
                <div class="bar-row">
                  <span>Rule Confidence</span>
                  <span>{{ Math.round(store.assessment.confidence_breakdown.rule_confidence * 100) }}%</span>
                </div>
                <div class="bar-track">
                  <div class="bar-fill" :style="{ width: (store.assessment.confidence_breakdown.rule_confidence * 100) + '%', background: barColor(store.assessment.confidence_breakdown.rule_confidence) }"></div>
                </div>
                <div class="bar-hint">Are zoning rules clearly stated or ambiguous?</div>
              </div>

              <div class="tooltip-sep"></div>

              <div class="bar-row overall-row">
                <span>Overall = Data Quality x Rule Confidence</span>
                <span>{{ Math.round(store.assessment.confidence_breakdown.overall * 100) }}%</span>
              </div>

              <div class="tooltip-sep"></div>

              <div class="factors-title">Factors</div>
              <ul class="factors">
                <li v-for="(f, i) in store.assessment.confidence_breakdown.factors" :key="i">{{ f }}</li>
              </ul>

              <div class="tooltip-sep"></div>

              <div class="grade-legend">
                <div><span class="gl" style="background:#16a34a">A</span> 90%+ — Complete data, clear rules</div>
                <div><span class="gl" style="background:#1a1a1a">B</span> 75-89% — Mostly clear, minor gaps</div>
                <div><span class="gl" style="background:#92400e">C</span> 60-74% — Missing data or ambiguous rules</div>
                <div><span class="gl" style="background:#dc2626">D</span> &lt;60% — Significant gaps</div>
              </div>
            </div>
          </span>
        </div>
      </div>
      <p class="summary">{{ store.assessment.summary }}</p>
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
            <td class="td-rule">{{ c.rule }}</td>
            <td>{{ c.value }}</td>
            <td>{{ c.applied_to_parcel }}</td>
            <td class="td-citation">{{ c.citation }}</td>
            <td>
              <span class="conf-tag" :style="{ color: confidenceColor(c.confidence) }">
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
    <p>Select a building type to run the assessment.</p>
  </div>
</template>

<style scoped>
.assessment-panel {
  background: #fff;
  border: 1px solid #eee;
  border-radius: 12px;
  overflow: hidden;
}

.assessment-panel.empty {
  padding: 32px;
  color: #999;
  text-align: center;
  font-size: 14px;
}

/* Verdict */
.verdict-section {
  padding: 32px;
  border-bottom: 1px solid #f0f0f0;
}

.verdict-top {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.grade-badge {
  color: #fff;
  font-weight: 700;
  font-size: 24px;
  width: 52px;
  height: 52px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.verdict-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.buildable-label {
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.3px;
}
.buildable-label.yes { color: #16a34a; }
.buildable-label.no { color: #dc2626; }

.confidence-score {
  font-size: 14px;
  color: #888;
  cursor: help;
  text-decoration: underline dotted #bbb;
  position: relative;
}

.summary {
  font-size: 15px;
  line-height: 1.7;
  color: #444;
}

/* Tooltip */
.tooltip {
  position: absolute;
  top: 100%;
  left: 0;
  z-index: 200;
  background: #1a1a1a;
  color: #eee;
  border-radius: 12px;
  padding: 20px;
  width: 380px;
  font-size: 13px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.4);
  margin-top: 8px;
  line-height: 1.5;
  text-decoration: none;
}

.tooltip-title { font-size: 15px; font-weight: 700; color: #fff; margin-bottom: 4px; }
.tooltip-desc { font-size: 12px; color: #888; margin-bottom: 16px; }

.bar-group { margin-bottom: 14px; }
.bar-row { display: flex; justify-content: space-between; font-weight: 600; font-size: 13px; margin-bottom: 4px; }
.bar-track { height: 6px; background: #333; border-radius: 3px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 3px; transition: width 0.3s; }
.bar-hint { font-size: 11px; color: #666; margin-top: 3px; }

.tooltip-sep { border-top: 1px solid #333; margin: 12px 0; }

.overall-row { font-size: 13px; font-weight: 700; color: #fff; }

.factors-title { font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: #777; margin-bottom: 6px; }
.factors { list-style: none; padding: 0; }
.factors li { font-size: 12px; color: #aaa; padding: 2px 0 2px 14px; position: relative; }
.factors li::before { content: ''; position: absolute; left: 0; top: 9px; width: 4px; height: 4px; border-radius: 50%; background: #555; }

.grade-legend { display: flex; flex-direction: column; gap: 3px; }
.grade-legend > div { font-size: 11px; color: #888; display: flex; align-items: center; gap: 6px; }
.gl { color: #fff; font-weight: 700; font-size: 9px; width: 16px; height: 16px; border-radius: 3px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }

/* Constraints */
.constraints-section {
  padding: 20px 24px;
}

h3 {
  font-size: 13px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #999;
  margin-bottom: 12px;
}

table { width: 100%; border-collapse: collapse; font-size: 13px; }

th {
  text-align: left;
  padding: 8px 10px;
  border-bottom: 1px solid #eee;
  font-weight: 500;
  color: #999;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

td { padding: 10px 10px; border-bottom: 1px solid #f5f5f5; color: #444; }
.td-rule { font-weight: 500; color: #1a1a1a; }
.td-citation { font-family: 'SF Mono', monospace; font-size: 12px; color: #666; }

.conf-tag { font-weight: 600; font-size: 12px; }

.type-tag {
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 4px;
  font-weight: 500;
}
.type-tag.interpretive { background: #fef3c7; color: #92400e; }
.type-tag.deterministic { background: #f0fdf4; color: #166534; }

/* Open Questions */
.open-questions {
  padding: 20px 24px;
  border-top: 1px solid #f0f0f0;
  background: #fafafa;
}

.open-questions ul { list-style: disc; padding-left: 20px; }
.open-questions li { font-size: 13px; line-height: 1.6; color: #666; margin-bottom: 4px; }
</style>
