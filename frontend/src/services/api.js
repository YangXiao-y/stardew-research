/*
 * 前端 API 服务层 (JavaScript)
 * 提供与后端 FastAPI 接口的交互
 */

// 后端 API 地址
const API_BASE_URL = 'http://localhost:8000/api'

// 创建研究
export async function startResearch(question, model = 'qwen', debug = false) {
  const response = await fetch(`${API_BASE_URL}/research`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      question,
      model,
      debug,
    }),
  })

  if (!response.ok) {
    throw new Error(`研究启动失败: ${response.statusText}`)
  }

  return await response.json()
}

// 单轮对话
export async function researchTurn(sessionId, question, useMemory = true) {
  const response = await fetch(`${API_BASE_URL}/research/turn`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      session_id: sessionId,
      question,
      use_memory: useMemory,
      model: 'qwen',
      debug: false,
    }),
  })

  if (!response.ok) {
    throw new Error(`对话失败: ${response.statusText}`)
  }

  return await response.json()
}

// 获取研究状态
export async function getResearchStatus(sessionId) {
  const response = await fetch(`${API_BASE_URL}/research/${sessionId}`)

  if (!response.ok) {
    throw new Error(`获取状态失败: ${response.statusText}`)
  }

  return await response.json()
}

// 获取会话列表
export async function listResearchSessions(limit = 10, offset = 0) {
  const response = await fetch(
    `${API_BASE_URL}/research?limit=${limit}&offset=${offset}`
  )

  if (!response.ok) {
    throw new Error(`获取会话列表失败: ${response.statusText}`)
  }

  return await response.json()
}

// 删除会话
export async function deleteSession(sessionId) {
  const response = await fetch(
    `${API_BASE_URL}/research/${sessionId}`,
    {
      method: 'DELETE',
    }
  )

  if (!response.ok) {
    throw new Error(`删除会话失败: ${response.statusText}`)
  }

  return await response.json()
}

// 导出会话
export async function exportSession(sessionId, format = 'json') {
  const response = await fetch(`${API_BASE_URL}/export`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      session_id: sessionId,
      format,
    }),
  })

  if (!response.ok) {
    throw new Error(`导出失败: ${response.statusText}`)
  }

  return await response.json()
}

// 获取系统状态
export async function getSystemStatus() {
  const response = await fetch(`${API_BASE_URL}/status`)

  if (!response.ok) {
    throw new Error(`获取系统状态失败: ${response.statusText}`)
  }

  return await response.json()
}
