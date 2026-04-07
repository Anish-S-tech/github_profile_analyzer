import axios from 'axios'

const BASE = 'http://localhost:8000'

export async function analyzeUser(username, useLlm = true) {
  const { data } = await axios.post(`${BASE}/analyze`, { username, use_llm: useLlm })
  return data
}

export async function checkHealth() {
  const { data } = await axios.get(`${BASE}/health`)
  return data
}
