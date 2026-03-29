import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  fetchAIQuestionsState,
  submitAIAnswers,
  type AIQuestion,
} from '../api/question'

// ─── 样式 ────────────────────────────────────────────────────
const c = {
  page: {
    minHeight: '100dvh',
    background: 'linear-gradient(160deg, #f0f4ff 0%, #fafafa 60%)',
    fontFamily: "'PingFang SC', 'Helvetica Neue', sans-serif",
    paddingBottom: 104,
  } as React.CSSProperties,

  header: {
    padding: '28px 20px 0',
    background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
    color: '#fff',
  } as React.CSSProperties,

  step: {
    fontSize: 12,
    opacity: 0.8,
    letterSpacing: 1,
    textTransform: 'uppercase' as const,
    marginBottom: 4,
  } as React.CSSProperties,

  headerTitle: { margin: '0 0 4px', fontSize: 20, fontWeight: 700 } as React.CSSProperties,
  headerSub: { margin: '0 0 16px', fontSize: 13, opacity: 0.85 } as React.CSSProperties,

  // ── 进度条 ──
  progressWrap: {
    height: 4,
    background: 'rgba(255,255,255,0.3)',
    borderRadius: 2,
    overflow: 'hidden',
    margin: '0 0 20px',
  } as React.CSSProperties,

  progressBar: (pct: number) => ({
    height: '100%',
    width: `${pct}%`,
    background: '#fff',
    borderRadius: 2,
    transition: 'width 0.35s ease',
  } as React.CSSProperties),

  // ── 题目计数 ──
  counter: {
    textAlign: 'right' as const,
    fontSize: 12,
    opacity: 0.75,
    paddingBottom: 16,
  } as React.CSSProperties,

  body: { padding: '16px 16px 0' } as React.CSSProperties,

  // ── 题目卡片 ──
  qCard: {
    background: '#fff',
    borderRadius: 16,
    padding: '20px 16px',
    boxShadow: '0 1px 4px rgba(0,0,0,0.06)',
    marginBottom: 12,
  } as React.CSSProperties,

  qText: {
    fontSize: 16,
    fontWeight: 700,
    color: '#111827',
    lineHeight: 1.6,
    marginBottom: 16,
  } as React.CSSProperties,

  optionBtn: (selected: boolean) => ({
    display: 'flex',
    alignItems: 'center',
    gap: 12,
    width: '100%',
    minHeight: 52,
    padding: '10px 14px',
    borderRadius: 12,
    border: selected ? '2px solid #6366f1' : '1.5px solid #e5e7eb',
    background: selected ? '#eef2ff' : '#fafafa',
    marginBottom: 10,
    cursor: 'pointer',
    textAlign: 'left' as const,
    transition: 'border-color 0.15s, background 0.15s, box-shadow 0.15s',
    boxShadow: selected ? '0 0 0 3px rgba(99,102,241,0.15)' : 'none',
  } as React.CSSProperties),

  optionCircle: (selected: boolean) => ({
    flexShrink: 0,
    width: 28,
    height: 28,
    borderRadius: '50%',
    background: selected ? '#6366f1' : '#e5e7eb',
    color: selected ? '#fff' : '#6b7280',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: 12,
    fontWeight: 700,
    transition: 'background 0.15s',
  } as React.CSSProperties),

  optionText: (selected: boolean) => ({
    flex: 1,
    fontSize: 14,
    color: selected ? '#3730a3' : '#374151',
    fontWeight: selected ? 600 : 400,
    lineHeight: 1.4,
  } as React.CSSProperties),

  checkIcon: { fontSize: 15, color: '#6366f1' } as React.CSSProperties,

  // ── 骨架屏 ──
  skelCard: {
    background: '#fff',
    borderRadius: 16,
    padding: 20,
    boxShadow: '0 1px 4px rgba(0,0,0,0.06)',
  } as React.CSSProperties,

  skelLine: (w: string, h = 16) => ({
    height: h,
    borderRadius: 8,
    width: w,
    marginBottom: 10,
    background: 'linear-gradient(90deg,#f3f4f6 25%,#e5e7eb 50%,#f3f4f6 75%)',
    backgroundSize: '200% 100%',
    animation: 'shimmer 1.4s infinite',
  } as React.CSSProperties),

  // ── 错误 ──
  errBox: {
    margin: '40px 16px',
    background: '#fff',
    border: '1.5px solid #fca5a5',
    borderRadius: 16,
    padding: 24,
    textAlign: 'center' as const,
  } as React.CSSProperties,

  retryBtn: {
    marginTop: 12,
    padding: '10px 28px',
    borderRadius: 10,
    border: '1.5px solid #6366f1',
    background: '#fff',
    color: '#6366f1',
    fontSize: 14,
    fontWeight: 600,
    cursor: 'pointer',
  } as React.CSSProperties,

  // ── 底部导航 ──
  footer: {
    position: 'fixed',
    bottom: 0,
    left: 0,
    right: 0,
    padding: '12px 16px 28px',
    background: 'rgba(255,255,255,0.96)',
    backdropFilter: 'blur(8px)',
    borderTop: '1px solid #f3f4f6',
    display: 'flex',
    gap: 10,
  } as React.CSSProperties,

  prevBtn: (hidden: boolean) => ({
    height: 52,
    minWidth: 80,
    borderRadius: 14,
    border: '1.5px solid #e5e7eb',
    background: '#fff',
    color: '#6b7280',
    fontSize: 15,
    fontWeight: 600,
    cursor: 'pointer',
    flexShrink: 0,
    visibility: hidden ? 'hidden' as const : 'visible' as const,
  } as React.CSSProperties),

  nextBtn: (disabled: boolean, isSubmit: boolean) => {
    let bg: string
    if (disabled) bg = '#e5e7eb'
    else if (isSubmit) bg = 'linear-gradient(135deg,#10b981 0%,#059669 100%)'
    else bg = 'linear-gradient(135deg,#6366f1 0%,#8b5cf6 100%)'
    return {
      flex: 1,
      height: 52,
      borderRadius: 14,
      border: 'none',
      background: bg,
      color: disabled ? '#9ca3af' : '#fff',
      fontSize: 16,
      fontWeight: 700,
      cursor: disabled ? 'not-allowed' : 'pointer',
      transition: 'background 0.2s',
    } as React.CSSProperties
  },
}

const shimmerCSS = `
@keyframes shimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}
`

// ─── 骨架屏 ─────────────────────────────────────────────────
function Skeleton() {
  return (
    <div style={{ padding: '16px 16px 0' }}>
      <div style={{ textAlign: 'center', padding: '12px 0 18px', color: '#6366f1', fontSize: 13 }}>
        ✨ AI 正在为你定制专属题目，请稍候…
      </div>
      <div style={c.skelCard}>
        <div style={c.skelLine('40%', 14)} />
        <div style={c.skelLine('85%', 20)} />
        <div style={c.skelLine('100%')} />
        <div style={c.skelLine('100%')} />
        <div style={c.skelLine('100%')} />
        <div style={{ ...c.skelLine('100%'), marginBottom: 0 }} />
      </div>
    </div>
  )
}

// ─── 主组件 ──────────────────────────────────────────────────
type LoadState = 'loading' | 'error' | 'success'

export default function AIQuestionPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const userId: string = location.state?.user_id ?? localStorage.getItem('user_id') ?? ''
  const sessionId: string = location.state?.session_id ?? localStorage.getItem('session_id') ?? ''

  const [loadState, setLoadState] = useState<LoadState>('loading')
  const [questions, setQuestions] = useState<AIQuestion[]>([])
  const [totalCount, setTotalCount] = useState(0)
  const [isGenerating, setIsGenerating] = useState(false)
  const [currentIndex, setCurrentIndex] = useState(0)
  // answers: question_id -> option_id
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [submitting, setSubmitting] = useState(false)
  const [waitingNext, setWaitingNext] = useState(false)

  const refreshQuestions = async (minCount = 1, forceLoading = false) => {
    if (forceLoading) setLoadState('loading')
    try {
      const data = await fetchAIQuestionsState(userId, sessionId || undefined, minCount)
      setQuestions(data.questions)
      setTotalCount(data.total_count)
      setIsGenerating(data.is_generating)

      if (data.questions.length > 0) {
        setLoadState('success')
        setWaitingNext(false)
      } else if (data.is_generating) {
        setLoadState('loading')
      } else {
        setLoadState('success')
      }
    } catch {
      setLoadState('error')
    }
  }

  useEffect(() => { void refreshQuestions(1, true) }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (loadState !== 'loading' || !sessionId) return
    const timer = globalThis.setInterval(() => {
      void refreshQuestions(1)
    }, 1500)
    return () => globalThis.clearInterval(timer)
  }, [loadState, sessionId])

  useEffect(() => {
    if (loadState !== 'success' || !isGenerating || !sessionId) return
    const desiredCount = Math.min(Math.max(currentIndex + 2, 1), totalCount || 1)
    const timer = globalThis.setInterval(() => {
      void refreshQuestions(desiredCount)
    }, 2000)
    return () => globalThis.clearInterval(timer)
  }, [loadState, isGenerating, sessionId, currentIndex, totalCount])

  const current = questions[currentIndex]
  const total = questions.length
  const progressBase = totalCount > 0 ? totalCount : total
  const progressPct = progressBase > 0 ? ((currentIndex + 1) / progressBase) * 100 : 0
  const selectedOption = current ? (answers[current.id] ?? '') : ''
  const isFirst = currentIndex === 0
  const isLast = currentIndex === total - 1

  function selectOption(optionId: string) {
    if (!current) return
    setAnswers(prev => ({ ...prev, [current.id]: optionId }))
  }

  function goPrev() {
    if (isFirst) return
    setCurrentIndex(i => i - 1)
  }

  async function goNext() {
    if (submitting || !selectedOption) return

    if (isLast && (isGenerating || total < totalCount)) {
      setWaitingNext(true)
      const nextState = await fetchAIQuestionsState(userId, sessionId || undefined, total + 1)
      setQuestions(nextState.questions)
      setTotalCount(nextState.total_count)
      setIsGenerating(nextState.is_generating)

      if (nextState.questions.length > total) {
        setCurrentIndex(i => i + 1)
        setWaitingNext(false)
      }
      return
    }

    if (isLast) {
      setSubmitting(true)
      try {
        const answersArr = Object.entries(answers).map(([question_id, option_id]) => ({
          question_id,
          option_id,
        }))
        const res = await submitAIAnswers({ user_id: userId, session_id: sessionId, answers: answersArr })
        navigate('/result', { state: { user_id: userId, session_id: res.session_id, top3: res.top3 } })
      } catch {
        navigate('/result', { state: { user_id: userId, session_id: sessionId, top3: [] } })
      } finally {
        setSubmitting(false)
      }
    } else {
      setCurrentIndex(i => i + 1)
    }
  }

  const nextLabel = (() => {
    if (submitting) return '提交中…'
    if (waitingNext) return '生成下一题中…'
    if (isLast && (isGenerating || total < totalCount)) return '下一题（生成中）'
    if (isLast) return '提交，匹配队友 🎉'
    return '下一题 →'
  })()

  return (
    <div style={c.page}>
      <style>{shimmerCSS}</style>

      {/* 顶部区域 */}
      <div style={c.header}>
        <div style={c.step}>Step 3 of 4</div>
        <h1 style={c.headerTitle}>AI 能力测评 ✨</h1>
        <p style={c.headerSub}>选出最符合你的选项，帮 AI 了解你</p>

        {/* 进度条 */}
        <div style={c.progressWrap}>
          <div style={c.progressBar(loadState === 'success' ? progressPct : 0)} />
        </div>

        {loadState === 'success' && total > 0 && (
          <div style={c.counter}>
            {currentIndex + 1} / {total}
          </div>
        )}
      </div>

      {/* 加载中 */}
      {loadState === 'loading' && <Skeleton />}

      {/* 加载失败 */}
      {loadState === 'error' && (
        <div style={c.errBox}>
          <div style={{ fontSize: 36, marginBottom: 8 }}>😢</div>
          <p style={{ color: '#ef4444', fontSize: 15, marginBottom: 0 }}>题目加载失败，请重试</p>
          <button style={c.retryBtn} onClick={() => void refreshQuestions(1, true)}>重新加载</button>
        </div>
      )}

      {/* AI 返回空题 */}
      {loadState === 'success' && total === 0 && (
        <div style={c.errBox}>
          <div style={{ fontSize: 36, marginBottom: 8 }}>⚠️</div>
          <p style={{ color: '#ef4444', fontSize: 15, marginBottom: 0 }}>AI 暂时不可用，未生成题目，请稍后重试</p>
          <button style={c.retryBtn} onClick={() => void refreshQuestions(1, true)}>重新加载</button>
        </div>
      )}

      {/* 题目 */}
      {loadState === 'success' && current && (
        <div style={c.body}>
          <div style={c.qCard}>
            <div style={c.qText}>{current.text}</div>

            {current.options.map(opt => {
              const selected = selectedOption === opt.option_id
              return (
                <button
                  key={opt.option_id}
                  style={c.optionBtn(selected)}
                  onClick={() => selectOption(opt.option_id)}
                >
                  <span style={c.optionCircle(selected)}>{opt.option_id}</span>
                  <span style={c.optionText(selected)}>{opt.text}</span>
                  {selected && <span style={c.checkIcon}>✓</span>}
                </button>
              )
            })}
          </div>
        </div>
      )}

      {/* 底部导航 */}
      {loadState === 'success' && total > 0 && (
        <div style={c.footer}>
          <button style={c.prevBtn(isFirst)} onClick={goPrev} disabled={isFirst}>
            ← 上一题
          </button>
          <button
            style={c.nextBtn(!selectedOption || submitting || waitingNext, isLast)}
            onClick={() => void goNext()}
            disabled={!selectedOption || submitting || waitingNext}
          >
            {nextLabel}
          </button>
        </div>
      )}
    </div>
  )
}
