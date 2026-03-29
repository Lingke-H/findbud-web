const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''  // 空字符串 = 相对路径，走 Vite proxy 避免 CORS

export interface QuestionOption {
  option_id: string
  text: string
}

export interface PreQuestion {
  question_id: string
  question_text: string
  options?: QuestionOption[]
  input_type?: 'choice' | 'slider'
  slider_min?: number
  slider_max?: number
  slider_step?: number
}

export interface SubmitPreAnswerPayload {
  user_id: string
  session_id?: string
  question_id: string
  selected_option_id: string
}

// MVP 阶段的硬编码兜底题目，当后端接口未就绪时使用
const MVP_FALLBACK_QUESTIONS: PreQuestion[] = [
  {
    question_id: 'pre_gender_preference',
    question_text: '对队友的性别要求？',
    input_type: 'choice',
    options: [
      { option_id: 'A', text: '女' },
      { option_id: 'B', text: '男' },
      { option_id: 'C', text: '我没有要求' },
    ],
  },
  {
    question_id: 'pre_grade_preference',
    question_text: '对队友的年级要求？',
    input_type: 'choice',
    options: [
      { option_id: 'A', text: '大一' },
      { option_id: 'B', text: '大二' },
      { option_id: 'C', text: '大三' },
      { option_id: 'D', text: '大四' },
      { option_id: 'E', text: '我没有要求' },
    ],
  },
  {
    question_id: 'pre_role',
    question_text: '你倾向在团队中担任什么角色？',
    input_type: 'choice',
    options: [
      { option_id: 'A', text: '建模手 — 负责数学建模与方案设计' },
      { option_id: 'B', text: '论文手 — 负责文字撰写与排版' },
      { option_id: 'C', text: '编程手 — 负责代码实现与数据处理' },
      { option_id: 'D', text: '无倾向 — 视团队需求灵活调整' },
    ],
  },
  {
    question_id: 'pre_personality_role',
    question_text: '你认为自己更倾向于在团队中扮演什么角色？',
    input_type: 'choice',
    options: [
      { option_id: 'A', text: '领导者' },
      { option_id: 'B', text: '执行者' },
      { option_id: 'C', text: '支持者' },
    ],
  },
  {
    question_id: 'pre_competition_count',
    question_text: '你过去有几场数学建模比赛经验？',
    input_type: 'slider',
    slider_min: 0,
    slider_max: 5,
    slider_step: 1,
  },
  {
    question_id: 'pre_has_award',
    question_text: '是否有过获奖？',
    input_type: 'choice',
    options: [
      { option_id: 'A', text: '是' },
      { option_id: 'B', text: '否' },
    ],
  },
]

/** 获取前置问题列表，后端就绪前返回本地 MVP 数据 */
export async function fetchPreQuestions(_userId: string): Promise<PreQuestion[]> {
  console.debug('[fetchPreQuestions] using mock data, API_BASE_URL=', API_BASE_URL)
  await new Promise(r => setTimeout(r, 600))
  return MVP_FALLBACK_QUESTIONS
}

/** 提交前置问题答案（MVP 阶段静默，不阻断流程） */
export async function submitPreAnswer(payload: SubmitPreAnswerPayload): Promise<void> {
  if (!payload.session_id) {
    await new Promise(r => setTimeout(r, 200))
    console.log('[submitPreAnswer] missing session_id, skip backend sync:', payload)
    return
  }

  const res = await fetch(`${API_BASE_URL}/api/v1/sessions/${payload.session_id}/pre-answer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      question_id: payload.question_id,
      option_id: payload.selected_option_id,
    }),
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err?.detail ?? `前置题提交失败 (${res.status})`)
  }
}

// ─── AI 选择题 ────────────────────────────────────────────────

export interface AIQuestion {
  id: string
  text: string
  dimension: string
  options: QuestionOption[]
}

export interface AnswerPayload {
  user_id: string
  session_id?: string
  answers: { question_id: string; option_id: string }[]
}

export interface AIQuestionsState {
  questions: AIQuestion[]
  total_count: number
  ready_count: number
  is_generating: boolean
}

/** 获取 AI 选择题状态（支持边生成边返回）。 */
export async function fetchAIQuestionsState(_userId: string, sessionId?: string, minCount = 1): Promise<AIQuestionsState> {
  if (!sessionId) {
    throw new Error('缺少 session_id')
  }

  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), 35000)  // 35s 超时（DeepSeek 较慢）
  try {
    const res = await fetch(
      `${API_BASE_URL}/api/v1/sessions/${sessionId}/questions?min_count=${Math.max(1, minCount)}`,
      { signal: controller.signal },
    )
    clearTimeout(timer)

    if (!res.ok) {
      throw new Error(`请求失败 (${res.status})`)
    }

    const data = await res.json() as AIQuestionsState
    if (!Array.isArray(data.questions)) {
      throw new Error('题目响应格式错误')
    }

    return {
      questions: data.questions,
      total_count: data.total_count ?? data.questions.length,
      ready_count: data.ready_count ?? data.questions.length,
      is_generating: Boolean(data.is_generating),
    }
  } catch {
    clearTimeout(timer)
    throw new Error('AI 题目接口请求失败')
  }
}

/** 兼容旧调用：仅返回题目列表 */
export async function fetchAIQuestions(_userId: string, sessionId?: string): Promise<AIQuestion[]> {
  const state = await fetchAIQuestionsState(_userId, sessionId, 1)
  return state.questions
}

export interface BackendCandidate {
  user_id: string
  name: string
  grade: string
  major: string
  match_score: number
  contact_info: string
  summary: string
  radar: { dimension: string; user: number; candidate: number }[]
}

export interface SubmitAIAnswersResponse {
  session_id: string
  top3: BackendCandidate[]
}

/** 提交全部 AI 问答答案，返回 session_id 与 Top3 匹配结果 */
export async function submitAIAnswers(payload: AnswerPayload): Promise<SubmitAIAnswersResponse> {
  const sid = payload.session_id ?? 'mock-session-id'
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/sessions/${sid}/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    if (res.ok) return res.json() as Promise<SubmitAIAnswersResponse>
  } catch {
    // 后端不可用时静默降级，使用 Mock 结果
  }
  console.log('[submitAIAnswers] fallback to mock, payload:', payload)
  await new Promise(r => setTimeout(r, 800))
  return { session_id: sid, top3: [] }  // 空 top3 → MatchResultPage 用前端 MOCK_TOP3_DATA
}
