import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  fetchPreQuestions,
  submitPreAnswer,
  type PreQuestion,
} from '../api/question'

// ─── 样式 ────────────────────────────────────────────────────
const s = {
  page: {
    minHeight: '100dvh',
    background: 'linear-gradient(160deg, #f0f4ff 0%, #fafafa 60%)',
    fontFamily: "'PingFang SC', 'Helvetica Neue', sans-serif",
    paddingBottom: 100,
  } as React.CSSProperties,

  header: {
    padding: '32px 20px 20px',
    background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
    color: '#fff',
  } as React.CSSProperties,

  step: {
    fontSize: 12,
    opacity: 0.8,
    marginBottom: 4,
    letterSpacing: 1,
    textTransform: 'uppercase' as const,
  } as React.CSSProperties,

  headerTitle: { margin: 0, fontSize: 20, fontWeight: 700 } as React.CSSProperties,
  headerSub: { margin: '6px 0 0', fontSize: 13, opacity: 0.85 } as React.CSSProperties,

  body: { padding: '20px 16px 0' } as React.CSSProperties,

  // ── 骨架屏 ──
  skeletonCard: {
    background: '#fff',
    borderRadius: 16,
    padding: 20,
    marginBottom: 12,
    boxShadow: '0 1px 4px rgba(0,0,0,0.06)',
  } as React.CSSProperties,

  skeletonLine: (w: string, h = 16) => ({
    height: h,
    borderRadius: 8,
    background: 'linear-gradient(90deg, #f3f4f6 25%, #e5e7eb 50%, #f3f4f6 75%)',
    backgroundSize: '200% 100%',
    animation: 'shimmer 1.4s infinite',
    width: w,
    marginBottom: 10,
  } as React.CSSProperties),

  // ── 错误状态 ──
  errorBox: {
    margin: '40px 16px',
    background: '#fff',
    border: '1.5px solid #fca5a5',
    borderRadius: 16,
    padding: 24,
    textAlign: 'center' as const,
  } as React.CSSProperties,

  errorIcon: { fontSize: 36, marginBottom: 8 } as React.CSSProperties,
  errorText: { color: '#ef4444', fontSize: 15, marginBottom: 16 } as React.CSSProperties,

  retryBtn: {
    padding: '10px 28px',
    borderRadius: 10,
    border: '1.5px solid #6366f1',
    background: '#fff',
    color: '#6366f1',
    fontSize: 14,
    fontWeight: 600,
    cursor: 'pointer',
  } as React.CSSProperties,

  // ── 题目卡片 ──
  questionCard: {
    background: '#fff',
    borderRadius: 16,
    padding: '20px 16px',
    marginBottom: 12,
    boxShadow: '0 1px 4px rgba(0,0,0,0.06)',
  } as React.CSSProperties,

  questionText: {
    fontSize: 17,
    fontWeight: 700,
    color: '#111827',
    lineHeight: 1.5,
    marginBottom: 16,
  } as React.CSSProperties,

  optionBtn: (selected: boolean) => ({
    display: 'flex',
    alignItems: 'center',
    gap: 12,
    width: '100%',
    minHeight: 56,
    padding: '12px 16px',
    borderRadius: 12,
    border: selected ? '2px solid #6366f1' : '1.5px solid #e5e7eb',
    background: selected ? '#eef2ff' : '#fafafa',
    cursor: 'pointer',
    marginBottom: 10,
    textAlign: 'left' as const,
    transition: 'all 0.15s',
    boxShadow: selected ? '0 0 0 3px rgba(99,102,241,0.15)' : 'none',
  } as React.CSSProperties),

  optionId: (selected: boolean) => ({
    flexShrink: 0,
    width: 30,
    height: 30,
    borderRadius: '50%',
    background: selected ? '#6366f1' : '#e5e7eb',
    color: selected ? '#fff' : '#6b7280',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: 13,
    fontWeight: 700,
  } as React.CSSProperties),

  optionText: (selected: boolean) => ({
    fontSize: 14,
    color: selected ? '#3730a3' : '#374151',
    fontWeight: selected ? 600 : 400,
    flex: 1,
  } as React.CSSProperties),

  checkMark: { fontSize: 16, color: '#6366f1', marginLeft: 'auto' } as React.CSSProperties,

  // ── 进度指示器 ──
  progress: {
    display: 'flex',
    gap: 6,
    justifyContent: 'center',
    padding: '4px 0 16px',
  } as React.CSSProperties,

  dot: (active: boolean, done: boolean) => ({
    width: active ? 20 : 8,
    height: 8,
    borderRadius: 4,
    background: done || active ? '#6366f1' : '#d1d5db',
    transition: 'all 0.2s',
  } as React.CSSProperties),

  // ── 底部按钮 ──
  footer: {
    position: 'fixed',
    bottom: 0,
    left: 0,
    right: 0,
    padding: '12px 16px 28px',
    background: 'rgba(255,255,255,0.95)',
    backdropFilter: 'blur(8px)',
    borderTop: '1px solid #f3f4f6',
  } as React.CSSProperties,

  nextBtn: (disabled: boolean) => ({
    width: '100%',
    height: 52,
    borderRadius: 14,
    border: 'none',
    background: disabled
      ? '#e5e7eb'
      : 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
    color: disabled ? '#9ca3af' : '#fff',
    fontSize: 17,
    fontWeight: 700,
    cursor: disabled ? 'not-allowed' : 'pointer',
    transition: 'all 0.2s',
  } as React.CSSProperties),
}

// ─── Shimmer 动画注入 ────────────────────────────────────────
const shimmerStyle = `
@keyframes shimmer {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
`

// ─── 骨架屏 ─────────────────────────────────────────────────
function Skeleton() {
  return (
    <div style={s.body}>
      <div style={s.skeletonCard}>
        <div style={s.skeletonLine('70%', 20)} />
        <div style={s.skeletonLine('100%')} />
        <div style={s.skeletonLine('100%')} />
        <div style={s.skeletonLine('100%')} />
        <div style={s.skeletonLine('100%')} />
      </div>
    </div>
  )
}

// ─── 主组件 ──────────────────────────────────────────────────
type LoadState = 'loading' | 'error' | 'success'

export default function PreQuestionPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const userId: string = location.state?.user_id ?? localStorage.getItem('user_id') ?? ''
  const sessionId: string = location.state?.session_id ?? localStorage.getItem('session_id') ?? ''

  const [loadState, setLoadState] = useState<LoadState>('loading')
  const [questions, setQuestions] = useState<PreQuestion[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [submitting, setSubmitting] = useState(false)

  const load = async () => {
    setLoadState('loading')
    try {
      const data = await fetchPreQuestions(userId)
      setQuestions(data)
      setLoadState('success')
    } catch {
      setLoadState('error')
    }
  }

  useEffect(() => { void load() }, [])  // eslint-disable-line react-hooks/exhaustive-deps

  const current = questions[currentIndex]
  const selectedOption = current ? (answers[current.question_id] ?? '') : ''
  const isLast = currentIndex === questions.length - 1
  const btnLabel = isLast ? '开始 AI 问答 →' : '下一题 →'

  async function handleNext() {
    if (submitting) return
    if (!selectedOption) return
    setSubmitting(true)
    try {
      await submitPreAnswer({
        user_id: userId,
        question_id: current.question_id,
        selected_option_id: selectedOption,
      })
      if (isLast) {
        navigate('/ai-question', {
          state: { user_id: userId, session_id: sessionId, pre_answers: answers },
        })
      } else {
        setCurrentIndex(i => i + 1)
      }
    } catch {
      navigate('/ai-question', {
        state: { user_id: userId, session_id: sessionId, pre_answers: answers },
      })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div style={s.page}>
      <style>{shimmerStyle}</style>

      {/* 顶部 */}
      <div style={s.header}>
        <div style={s.step}>Step 2 of 4</div>
        <h1 style={s.headerTitle}>了解你的风格 🎯</h1>
        <p style={s.headerSub}>帮助我们更精准地为你匹配队友</p>
      </div>

      {/* 加载中 */}
      {loadState === 'loading' && <Skeleton />}

      {/* 加载失败 */}
      {loadState === 'error' && (
        <div style={s.errorBox}>
          <div style={s.errorIcon}>😢</div>
          <p style={s.errorText}>题目加载失败，请检查网络后重试</p>
          <button style={s.retryBtn} onClick={() => void load()}>
            重新加载
          </button>
        </div>
      )}

      {/* 加载成功 */}
      {loadState === 'success' && current && (
        <div style={s.body}>

          {/* 进度点 */}
          {questions.length > 1 && (
            <div style={s.progress}>
              {questions.map((q, i) => (
                <div key={q.question_id} style={s.dot(i === currentIndex, i < currentIndex)} />
              ))}
            </div>
          )}

          {/* 题目卡片 */}
          <div style={s.questionCard}>
            <div style={s.questionText}>{current.question_text}</div>

            {current.options.map(opt => {
              const selected = selectedOption === opt.option_id
              return (
                <button
                  key={opt.option_id}
                  style={s.optionBtn(selected)}
                  onClick={() =>
                    setAnswers(prev => ({
                      ...prev,
                      [current.question_id]: opt.option_id,
                    }))
                  }
                >
                  <span style={s.optionId(selected)}>{opt.option_id}</span>
                  <span style={s.optionText(selected)}>{opt.text}</span>
                  {selected && <span style={s.checkMark}>✓</span>}
                </button>
              )
            })}
          </div>
        </div>
      )}

      {/* 底部按钮 */}
      {loadState === 'success' && (
        <div style={s.footer}>
          <button
            style={s.nextBtn(!selectedOption || submitting)}
            onClick={() => void handleNext()}
            disabled={!selectedOption || submitting}
          >
            {submitting ? '提交中…' : btnLabel}
          </button>
        </div>
      )}
    </div>
  )
}
