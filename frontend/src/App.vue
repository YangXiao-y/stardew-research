<!-- 前端主应用 App.vue -->

<template>
  <div class="app">
    <!-- 顶部导航 -->
    <header class="navbar">
      <div class="navbar-brand">
        <h1>🌾AI 游戏攻略助手</h1>
        <p class="subtitle">Multi-Agent AI Research System</p>
      </div>
      <div class="navbar-links">
        <a href="#/" :class="{ active: currentPage === 'research' }" @click="currentPage = 'research'">
          新建研究
        </a>
        <a href="#/" :class="{ active: currentPage === 'sessions' }" @click="currentPage = 'sessions'">
          会话管理
        </a>
        <a href="#/" :class="{ active: currentPage === 'status' }" @click="currentPage = 'status'">
          系统状态
        </a>
      </div>
    </header>

    <!-- 主内容区域 -->
    <main class="main-content">
      <!-- 研究页面 -->
      <div v-if="currentPage === 'research'" class="page">
        <div class="panel">
          <h2>启动新研究</h2>

          <!-- 输入表单 -->
          <div class="form-group">
            <label>研究问题</label>
            <textarea
              v-model="researchForm.question"
              placeholder="输入你的问题，例如：第一年春季最赚钱的农作物是什么？"
              rows="4"
              class="textarea"
            ></textarea>
          </div>

          <div class="form-group">
            <label>目标游戏</label>
            <input
              v-model="researchForm.game"
              placeholder="例如：Stardew Valley / 原神 / 塞尔达传说"
              class="input"
            />
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>LLM 模型</label>
              <select v-model="researchForm.model" class="select">
                <option value="qwen">QWen Plus</option>
                <option value="gpt4">GPT-4</option>
                <option value="claude">Claude 3</option>
              </select>
            </div>

            <div class="form-group">
              <label>
                <input type="checkbox" v-model="researchForm.debug" />
                启用调试模式
              </label>
            </div>
          </div>

          <button @click="startResearch_()" :disabled="isLoading" class="btn btn-primary">
            <span v-if="!isLoading">🚀 开始研究</span>
            <span v-else>⏳ 研究中...</span>
          </button>

          <!-- 错误提示 -->
          <div v-if="error" class="alert alert-error">
            ❌ {{ error }}
          </div>

          <!-- 研究结果 -->
          <div v-if="currentResult" class="result-panel">
            <div class="result-header">
              <h3>✅ 研究完成</h3>
              <p class="session-id">会话 ID: {{ currentResult.session_id }}</p>
            </div>

            <div class="result-info">
              <div class="info-item">
                <span class="label">问题类型:</span>
                <span class="value">{{ currentResult.question_type }}</span>
              </div>
              <div class="info-item">
                <span class="label">子任务数:</span>
                <span class="value">{{ currentResult.subtasks_count }}</span>
              </div>
              <div class="info-item">
                <span class="label">收集证据:</span>
                <span class="value">{{ currentResult.evidence_count }} 条</span>
              </div>
            </div>

            <div class="result-answer">
              <h4>🎯 研究答案</h4>
              <div class="answer-content">{{ currentResult.answer }}</div>
            </div>

            <div class="result-actions">
              <button @click="continueTurn(currentResult.session_id)" class="btn btn-secondary">
                💬 继续对话
              </button>
              <button @click="exportResult(currentResult.session_id)" class="btn btn-secondary">
                📤 导出结果
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 会话管理页面 -->
      <div v-if="currentPage === 'sessions'" class="page">
        <div class="panel">
          <h2>会话管理</h2>

          <button @click="loadSessions_()" class="btn btn-secondary">
            🔄 刷新会话列表
          </button>

          <div v-if="sessions.length === 0" class="empty-state">
            <p>暂无会话</p>
          </div>

          <div v-else class="sessions-list">
            <div v-for="session in sessions" :key="session.session_id" class="session-card">
              <div class="session-header">
                <h4>{{ session.first_question }}</h4>
                <span class="session-time">{{ new Date(session.created_at).toLocaleString() }}</span>
              </div>

              <div class="session-meta">
                <span>轮次: {{ session.turns }}</span>
              </div>

              <div class="session-actions">
                <button
                  @click="viewSession(session.session_id)"
                  class="btn btn-small btn-primary"
                >
                  查看
                </button>
                <button
                  @click="deleteSession_(session.session_id)"
                  class="btn btn-small btn-danger"
                >
                  删除
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 系统状态页面 -->
      <div v-if="currentPage === 'status'" class="page">
        <div class="panel">
          <h2>系统状态</h2>

          <div class="status-grid">
            <div class="status-card">
              <div class="status-icon">📊</div>
              <div class="status-content">
                <div class="status-label">所有会话</div>
                <div class="status-value">{{ systemStats.total_sessions }}</div>
              </div>
            </div>

            <div class="status-card">
              <div class="status-icon">🚀</div>
              <div class="status-content">
                <div class="status-label">活跃会话</div>
                <div class="status-value">{{ systemStats.active_sessions }}</div>
              </div>
            </div>

            <div class="status-card">
              <div class="status-icon">💾</div>
              <div class="status-content">
                <div class="status-label">已用 Token</div>
                <div class="status-value">{{ systemStats.total_tokens_used }}</div>
              </div>
            </div>

            <div class="status-card">
              <div class="status-icon">⏱️</div>
              <div class="status-content">
                <div class="status-label">平均响应时间</div>
                <div class="status-value">{{ systemStats.average_response_time.toFixed(2) }}s</div>
              </div>
            </div>
          </div>

          <div class="models-section">
            <h3>可用模型</h3>
            <div class="models-list">
              <div v-for="model in systemStats.available_models" :key="model.name" class="model-tag">
                <span v-if="model.available" class="status-badge green">✓</span>
                <span v-else class="status-badge red">✗</span>
                {{ model.name }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- 底部 -->
    <footer class="footer">
      <p>© 2024 Stardew Valley AI Research Assistant | v2.0.0</p>
      <p>powered by AutoGen + MCP + Skill</p>
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import {
  startResearch,
  researchTurn,
  listResearchSessions,
  deleteSession as apiDeleteSession,
  getSystemStatus,
  getResearchStatus,
} from './services/api'

// 页面状态
const currentPage = ref('research')
const isLoading = ref(false)
const error = ref(null)

// 研究表单
const researchForm = ref({
  question: '',
  game: 'Stardew Valley',
  model: 'qwen',
  debug: false,
})

// 结果
const currentResult = ref(null)
const sessions = ref([])
const systemStats = ref({
  total_sessions: 0,
  active_sessions: 0,
  total_tokens_used: 0,
  average_response_time: 0,
  available_models: [],
})

// 启动研究
async function startResearch_() {
  if (!researchForm.value.question.trim()) {
    error.value = '请输入研究问题'
    return
  }

  isLoading.value = true
  error.value = null

  try {
    const result = await startResearch(
      researchForm.value.question,
      researchForm.value.model,
      researchForm.value.debug,
      researchForm.value.game
    )

    currentResult.value = result
    researchForm.value.question = ''
  } catch (err) {
    error.value = err.message
  } finally {
    isLoading.value = false
  }
}

// 继续对话
async function continueTurn(sessionId) {
  const nextQuestion = prompt('请输入下一个问题:')
  if (!nextQuestion) return

  isLoading.value = true
  error.value = null

  try {
    const result = await researchTurn(
      sessionId,
      nextQuestion,
      true,
      currentResult.value?.game || researchForm.value.game
    )
    currentResult.value = {
      ...currentResult.value,
      game: result.game || currentResult.value?.game || researchForm.value.game,
      answer: result.answer,
    }
  } catch (err) {
    error.value = err.message
  } finally {
    isLoading.value = false
  }
}

// 加载会话列表
async function loadSessions_() {
  isLoading.value = true
  error.value = null

  try {
    const data = await listResearchSessions()
    sessions.value = data.sessions
  } catch (err) {
    error.value = err.message
  } finally {
    isLoading.value = false
  }
}

// 删除会话
async function deleteSession_(sessionId) {
  if (!confirm('确定要删除此会话吗?')) return

  isLoading.value = true
  error.value = null

  try {
    await apiDeleteSession(sessionId)
    await loadSessions_()
  } catch (err) {
    error.value = err.message
  } finally {
    isLoading.value = false
  }
}

// 查看会话
async function viewSession(sessionId) {
  currentPage.value = 'research'
  isLoading.value = true

  try {
    const result = await getResearchStatus(sessionId)
    currentResult.value = result
  } catch (err) {
    error.value = err.message
  } finally {
    isLoading.value = false
  }
}

// 导出结果
async function exportResult(sessionId) {
  // 在实际应用中，这会下载文件
  alert(`导出会话 ${sessionId} 的功能开发中...`)
}

// 页面挂载
onMounted(async () => {
  try {
    const stats = await getSystemStatus()
    systemStats.value = stats.engine_stats || systemStats.value
  } catch (err) {
    console.error('获取系统状态失败:', err)
  }
})
</script>

<style scoped>
/* 公共样式 */
:root {
  --primary-color: #4ade80;
  --secondary-color: #64748b;
  --error-color: #ef4444;
  --border-color: #e2e8f0;
  --bg-color: #f8fafc;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.app {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background-color: var(--bg-color);
}

/* 导航栏 */
.navbar {
  background: white;
  border-bottom: 1px solid var(--border-color);
  padding: 1.5rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.navbar-brand h1 {
  font-size: 1.5rem;
  margin-bottom: 0.25rem;
}

.subtitle {
  font-size: 0.875rem;
  color: var(--secondary-color);
}

.navbar-links {
  display: flex;
  gap: 1.5rem;
}

.navbar-links a {
  text-decoration: none;
  color: var(--secondary-color);
  font-weight: 500;
  cursor: pointer;
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  transition: all 0.2s;
}

.navbar-links a.active {
  background-color: var(--primary-color);
  color: white;
}

/* 主内容 */
.main-content {
  flex: 1;
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
  width: 100%;
}

.page {
  width: 100%;
}

.panel {
  background: white;
  border-radius: 0.5rem;
  padding: 2rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.panel h2 {
  margin-bottom: 1.5rem;
  color: #1e293b;
}

/* 表单 */
.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #334155;
}

.textarea,
.input,
.select {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid var(--border-color);
  border-radius: 0.375rem;
  font-size: 1rem;
  font-family: inherit;
}

.textarea {
  resize: vertical;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-bottom: 1rem;
}

/* 按钮 */
.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 0.375rem;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background-color: var(--primary-color);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: #22c55e;
}

.btn-secondary {
  background-color: var(--secondary-color);
  color: white;
}

.btn-secondary:hover {
  background-color: #475569;
}

.btn-danger {
  background-color: var(--error-color);
  color: white;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-small {
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
}

/* 警告 */
.alert {
  padding: 1rem;
  border-radius: 0.375rem;
  margin-top: 1rem;
}

.alert-error {
  background-color: #fee2e2;
  color: #991b1b;
  border: 1px solid #fecaca;
}

/* 结果面板 */
.result-panel {
  margin-top: 2rem;
  padding: 1.5rem;
  background-color: #f0fdf4;
  border-radius: 0.5rem;
  border: 1px solid #bbf7d0;
}

.result-header {
  margin-bottom: 1rem;
}

.result-header h3 {
  margin-bottom: 0.5rem;
  color: #166534;
}

.session-id {
  font-size: 0.875rem;
  color: #4b5563;
  font-family: monospace;
}

.result-info {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.info-item {
  display: flex;
  flex-direction: column;
}

.info-item .label {
  font-size: 0.875rem;
  color: #64748b;
  margin-bottom: 0.25rem;
}

.info-item .value {
  font-weight: 600;
  color: #1e293b;
}

.result-answer {
  margin-bottom: 1.5rem;
}

.result-answer h4 {
  margin-bottom: 0.75rem;
  color: #1e293b;
}

.answer-content {
  padding: 1rem;
  background-color: white;
  border-radius: 0.375rem;
  line-height: 1.6;
  color: #334155;
  max-height: 400px;
  overflow-y: auto;
}

.result-actions {
  display: flex;
  gap: 1rem;
}

/* 会话列表 */
.sessions-list {
  display: grid;
  gap: 1rem;
  margin-top: 1rem;
}

.session-card {
  padding: 1.5rem;
  border: 1px solid var(--border-color);
  border-radius: 0.375rem;
  background-color: white;
}

.session-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.session-header h4 {
  flex: 1;
  color: #1e293b;
}

.session-time {
  font-size: 0.875rem;
  color: #64748b;
}

.session-meta {
  margin-bottom: 1rem;
  font-size: 0.875rem;
  color: #64748b;
}

.session-actions {
  display: flex;
  gap: 0.5rem;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 2rem;
  color: #64748b;
}

/* 状态网格 */
.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.status-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.5rem;
  background: white;
  border-radius: 0.5rem;
  border: 1px solid var(--border-color);
}

.status-icon {
  font-size: 2rem;
}

.status-label {
  font-size: 0.875rem;
  color: #64748b;
  margin-bottom: 0.25rem;
}

.status-value {
  font-size: 1.5rem;
  font-weight: 600;
  color: #1e293b;
}

/* 模型列表 */
.models-section {
  margin-top: 2rem;
}

.models-section h3 {
  margin-bottom: 1rem;
}

.models-list {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.model-tag {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background-color: white;
  border: 1px solid var(--border-color);
  border-radius: 9999px;
  font-size: 0.875rem;
}

.status-badge {
  display: inline-block;
  width: 1rem;
  height: 1rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  color: white;
}

.status-badge.green {
  background-color: var(--primary-color);
}

.status-badge.red {
  background-color: var(--error-color);
}

/* 底部 */
.footer {
  text-align: center;
  padding: 1.5rem;
  color: var(--secondary-color);
  border-top: 1px solid var(--border-color);
  background: white;
  font-size: 0.875rem;
}

/* 响应式 */
@media (max-width: 768px) {
  .navbar {
    flex-direction: column;
    gap: 1rem;
  }

  .form-row {
    grid-template-columns: 1fr;
  }

  .result-info {
    grid-template-columns: 1fr;
  }

  .session-header {
    flex-direction: column;
    gap: 0.5rem;
  }

  .status-grid {
    grid-template-columns: 1fr;
  }
}
</style>
