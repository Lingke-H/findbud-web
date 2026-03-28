const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''  // 空字符串 = 相对路径，走 Vite proxy 避免 CORS

export interface QuestionOption {
  option_id: string
  text: string
}

export interface PreQuestion {
  question_id: string
  question_text: string
  options: QuestionOption[]
}

export interface SubmitPreAnswerPayload {
  user_id: string
  question_id: string
  selected_option_id: string
}

// MVP 阶段的硬编码兜底题目，当后端接口未就绪时使用
const MVP_FALLBACK_QUESTIONS: PreQuestion[] = [
  {
    question_id: 'pre_role',
    question_text: '你倾向在团队中担任什么角色？',
    options: [
      { option_id: 'A', text: '建模手 — 负责数学建模与方案设计' },
      { option_id: 'B', text: '论文手 — 负责文字撰写与排版' },
      { option_id: 'C', text: '编程手 — 负责代码实现与数据处理' },
      { option_id: 'D', text: '无倾向 — 视团队需求灵活调整' },
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
  await new Promise(r => setTimeout(r, 400))
  console.log('[submitPreAnswer] payload:', payload)
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

// MVP 兜底题目：覆盖三大向量维度（技能 / 性格动能 / 绝对实力）
const MVP_AI_QUESTIONS: AIQuestion[] = [
  {
    id: 'q_skill_model',
    dimension: '技能向量',
    text: '在数学建模中，面对一道从未见过的赛题，你通常第一步会怎么做？',
    options: [
      { option_id: 'A', text: '快速查阅相关文献，寻找已有模型框架' },
      { option_id: 'B', text: '先画出问题结构图，再讨论建模思路' },
      { option_id: 'C', text: '直接动手写代码，边跑数据边理解题意' },
      { option_id: 'D', text: '等队友讨论出方向再开始分工配合' },
    ],
  },
  {
    id: 'q_skill_code',
    dimension: '技能向量',
    text: '当队伍需要对大规模数据做可视化分析时，你最有把握的工具是？',
    options: [
      { option_id: 'A', text: 'Python（Pandas + Matplotlib / Seaborn）' },
      { option_id: 'B', text: 'MATLAB / R' },
      { option_id: 'C', text: 'Excel / WPS 图表功能' },
      { option_id: 'D', text: '我更擅长分析和写作，数据处理由队友负责' },
    ],
  },
  {
    id: 'q_skill_paper',
    dimension: '技能向量',
    text: '撰写论文时，你最擅长哪个部分？',
    options: [
      { option_id: 'A', text: '模型建立与公式推导' },
      { option_id: 'B', text: '摘要与整体行文逻辑' },
      { option_id: 'C', text: '图表制作与结果分析' },
      { option_id: 'D', text: '参考文献整理与格式排版' },
    ],
  },
  {
    id: 'q_personality',
    dimension: '性格动能',
    text: '团队在方向选择上出现分歧，你通常会？',
    options: [
      { option_id: 'A', text: '主动发表意见，推动大家达成决策' },
      { option_id: 'B', text: '先倾听各方观点，再提出折中方案' },
      { option_id: 'C', text: '跟随多数人意见，专注于执行' },
      { option_id: 'D', text: '根据数据和逻辑分析提出建议' },
    ],
  },
  {
    id: 'q_strength_ambition',
    dimension: '绝对实力',
    text: '你参加这次数学建模比赛最主要的目标是？',
    options: [
      { option_id: 'A', text: '冲击国家级奖项，简历加分' },
      { option_id: 'B', text: '提升建模能力，重在学习' },
      { option_id: 'C', text: '认识志同道合的朋友' },
      { option_id: 'D', text: '体验比赛流程，没有特别期待' },
    ],
  },
]

/** 获取 AI 选择题列表；session 有效时调用后端，12s 超时或失败后降级 MVP 本地数据 */
export async function fetchAIQuestions(_userId: string, sessionId?: string): Promise<AIQuestion[]> {
  if (sessionId) {
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), 35000)  // 35s 超时（DeepSeek 较慢）
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/v1/sessions/${sessionId}/questions`,
        { signal: controller.signal },
      )
      clearTimeout(timer)
      if (res.ok) {
        const data = await res.json() as { questions: AIQuestion[] }
        if (data.questions?.length) return data.questions
      }
    } catch {
      clearTimeout(timer)
      // 超时或后端不可用时降级到本地 mock
    }
  }
  console.debug('[fetchAIQuestions] using mock fallback, API_BASE_URL=', API_BASE_URL)
  await new Promise(r => setTimeout(r, 300))
  return MVP_AI_QUESTIONS
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
