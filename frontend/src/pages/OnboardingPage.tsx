import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { submitBaseInfo, type UserBaseInfoPayload } from '../api/user'

// ─── 选项常量 ───────────────────────────────────────────────
const GENDER_OPTIONS = ['男', '女', '非二元性别', '不愿透露']
const GRADE_OPTIONS = ['大一', '大二', '大三', '大四', '研究生']
const COMPETITION_OPTIONS = [
  { value: '数学建模', label: '📐 数学建模', available: true },
  { value: '编程竞赛', label: '💻 编程竞赛', available: false },
  { value: '创业大赛', label: '🚀 创业大赛', available: false },
]

// ─── 必填字段校验 ────────────────────────────────────────────
function isFormValid(f: Partial<UserBaseInfoPayload>): f is UserBaseInfoPayload {
  return (
    !!f.name?.trim() &&
    !!f.gender &&
    !!f.grade &&
    !!f.major?.trim() &&
    !!f.competition_target &&
    f.want_long_term !== undefined
  )
}

// ─── 样式工具 ────────────────────────────────────────────────
const s = {
  page: {
    minHeight: '100dvh',
    background: 'linear-gradient(160deg, #f0f4ff 0%, #fafafa 60%)',
    fontFamily: "'PingFang SC', 'Helvetica Neue', sans-serif",
    paddingBottom: 96,
  } as React.CSSProperties,

  header: {
    padding: '32px 20px 20px',
    background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
    color: '#fff',
  } as React.CSSProperties,

  headerTitle: { margin: 0, fontSize: 22, fontWeight: 700 } as React.CSSProperties,
  headerSub: { margin: '6px 0 0', fontSize: 14, opacity: 0.85 } as React.CSSProperties,

  body: { padding: '16px 16px 0' } as React.CSSProperties,

  card: {
    background: '#fff',
    borderRadius: 16,
    padding: '20px 16px',
    marginBottom: 12,
    boxShadow: '0 1px 4px rgba(0,0,0,0.06)',
  } as React.CSSProperties,

  label: {
    display: 'block',
    fontSize: 14,
    fontWeight: 600,
    color: '#374151',
    marginBottom: 10,
  } as React.CSSProperties,

  required: { color: '#ef4444', marginLeft: 2 } as React.CSSProperties,

  input: {
    width: '100%',
    minHeight: 48,
    padding: '0 14px',
    border: '1.5px solid #e5e7eb',
    borderRadius: 10,
    fontSize: 16,
    color: '#111827',
    background: '#fafafa',
    boxSizing: 'border-box',
    outline: 'none',
    transition: 'border-color 0.2s',
  } as React.CSSProperties,

  radioGroup: { display: 'flex', flexWrap: 'wrap', gap: 8 } as React.CSSProperties,

  radioBtn: (selected: boolean) => ({
    minHeight: 44,
    padding: '0 16px',
    borderRadius: 22,
    border: selected ? '2px solid #6366f1' : '1.5px solid #e5e7eb',
    background: selected ? '#eef2ff' : '#fafafa',
    color: selected ? '#4338ca' : '#6b7280',
    fontSize: 14,
    fontWeight: selected ? 600 : 400,
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    transition: 'all 0.15s',
  } as React.CSSProperties),

  compCard: (selected: boolean, disabled: boolean) => {
    let bg: string
    if (disabled) bg = '#f9fafb'
    else if (selected) bg = '#eef2ff'
    else bg = '#fafafa'
    let color: string
    if (disabled) color = '#d1d5db'
    else if (selected) color = '#4338ca'
    else color = '#374151'
    return {
    flex: '1 1 calc(33% - 8px)',
    minHeight: 56,
    border: selected ? '2px solid #6366f1' : '1.5px solid #e5e7eb',
    borderRadius: 12,
    background: bg,
    color,
    fontSize: 13,
    fontWeight: selected ? 600 : 400,
    cursor: disabled ? 'not-allowed' : 'pointer',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 2,
    padding: 8,
    transition: 'all 0.15s',
    position: 'relative',
  } as React.CSSProperties
  },

  toggleRow: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
  } as React.CSSProperties,

  toggleLabel: { fontSize: 15, color: '#374151' } as React.CSSProperties,
  toggleSub: { fontSize: 12, color: '#9ca3af', marginTop: 2 } as React.CSSProperties,

  toggleTrack: (on: boolean) => ({
    width: 52,
    height: 30,
    borderRadius: 15,
    background: on ? '#6366f1' : '#d1d5db',
    position: 'relative',
    cursor: 'pointer',
    transition: 'background 0.2s',
    flexShrink: 0,
  } as React.CSSProperties),

  toggleThumb: (on: boolean) => ({
    position: 'absolute',
    top: 3,
    left: on ? 25 : 3,
    width: 24,
    height: 24,
    borderRadius: '50%',
    background: '#fff',
    boxShadow: '0 1px 3px rgba(0,0,0,0.2)',
    transition: 'left 0.2s',
  } as React.CSSProperties),

  footer: {
    position: 'fixed',
    bottom: 0,
    left: 0,
    right: 0,
    padding: '12px 16px 24px',
    background: 'rgba(255,255,255,0.95)',
    backdropFilter: 'blur(8px)',
    borderTop: '1px solid #f3f4f6',
  } as React.CSSProperties,

  submitBtn: (disabled: boolean) => ({
    width: '100%',
    height: 52,
    borderRadius: 14,
    border: 'none',
    background: disabled ? '#e5e7eb' : 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
    color: disabled ? '#9ca3af' : '#fff',
    fontSize: 17,
    fontWeight: 700,
    cursor: disabled ? 'not-allowed' : 'pointer',
    transition: 'all 0.2s',
    letterSpacing: 0.5,
  } as React.CSSProperties),

  errorText: {
    fontSize: 12,
    color: '#ef4444',
    marginTop: 8,
    textAlign: 'center',
  } as React.CSSProperties,
}

// ─── 主组件 ──────────────────────────────────────────────────
export default function OnboardingPage() {
  const navigate = useNavigate()

  const [form, setForm] = useState<Partial<UserBaseInfoPayload>>({
    competition_target: '数学建模',
    want_long_term: false,
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const set = <K extends keyof UserBaseInfoPayload>(k: K, v: UserBaseInfoPayload[K]) =>
    setForm(prev => ({ ...prev, [k]: v }))

  const valid = isFormValid(form)

  async function handleSubmit() {
    if (!valid || loading) return
    setLoading(true)
    setError('')
    let userId: string = crypto.randomUUID()  // 本地兜底 ID，后端就绪时替换
    let sessionId: string = ''
    try {
      const res = await submitBaseInfo(form)
      userId = res.user_id
      sessionId = res.session_id
    } catch {
      // 后端不可用时使用本地 UUID，保证流程不中断
    }
    localStorage.setItem('user_id', userId)
    localStorage.setItem('session_id', sessionId)
    navigate('/question', { state: { user_id: userId, session_id: sessionId } })
    setLoading(false)
  }

  return (
    <div style={s.page}>
      {/* 顶部标题区 */}
      <div style={s.header}>
        <h1 style={s.headerTitle}>FindBud 找搭子</h1>
        <p style={s.headerSub}>填写基础信息，让 AI 为你匹配最佳队友 🎯</p>
      </div>

      <div style={s.body}>

        {/* 姓名 */}
        <div style={s.card}>
          <label htmlFor="input-name" style={s.label}>
            姓名 <span style={s.required}>*</span>
          </label>
          <input
            id="input-name"
            style={s.input}
            type="text"
            placeholder="请输入你的姓名"
            value={form.name ?? ''}
            onChange={e => set('name', e.target.value)}
          />
        </div>

        {/* 专业 */}
        <div style={s.card}>
          <label htmlFor="input-major" style={s.label}>
            专业 <span style={s.required}>*</span>
          </label>
          <input
            id="input-major"
            style={s.input}
            type="text"
            placeholder="数学与应用数学 / Mathematics and Applied Mathematics"
            value={form.major ?? ''}
            onChange={e => set('major', e.target.value)}
          />
        </div>

        {/* 性别 */}
        <div style={s.card}>
          <div style={s.label}>
            性别 <span style={s.required}>*</span>
          </div>
          <div style={s.radioGroup}>
            {GENDER_OPTIONS.map(g => (
              <button
                key={g}
                style={s.radioBtn(form.gender === g)}
                onClick={() => set('gender', g)}
              >
                {g}
              </button>
            ))}
          </div>
        </div>

        {/* 年级 */}
        <div style={s.card}>
          <div style={s.label}>
            年级 <span style={s.required}>*</span>
          </div>
          <div style={s.radioGroup}>
            {GRADE_OPTIONS.map(g => (
              <button
                key={g}
                style={s.radioBtn(form.grade === g)}
                onClick={() => set('grade', g)}
              >
                {g}
              </button>
            ))}
          </div>
        </div>

        {/* 组队目标 */}
        <div style={s.card}>
          <div style={s.label}>
            组队目标 <span style={s.required}>*</span>
          </div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {COMPETITION_OPTIONS.map(opt => (
              <button
                key={opt.value}
                style={s.compCard(form.competition_target === opt.value, !opt.available)}
                onClick={() => opt.available && set('competition_target', opt.value)}
                disabled={!opt.available}
              >
                <span style={{ fontSize: 20 }}>{opt.label.split(' ')[0]}</span>
                <span>{opt.label.split(' ')[1]}</span>
                {!opt.available && (
                  <span style={{ fontSize: 10, color: '#d1d5db', marginTop: 2 }}>即将上线</span>
                )}
              </button>
            ))}
          </div>
        </div>

        {/* 是否长期组队 */}
        <div style={s.card}>
          <div style={s.toggleRow}>
            <div>
              <div style={s.toggleLabel}>是否想要长期组队？</div>
              <div style={s.toggleSub}>开启后将优先匹配有持续合作意愿的队友</div>
            </div>
            <div
              style={s.toggleTrack(!!form.want_long_term)}
              onClick={() => set('want_long_term', !form.want_long_term)}
              role="switch"
              aria-checked={!!form.want_long_term}
              tabIndex={0}
              onKeyDown={e => (e.key === ' ' || e.key === 'Enter') && set('want_long_term', !form.want_long_term)}
            >
              <div style={s.toggleThumb(!!form.want_long_term)} />
            </div>
          </div>
        </div>

      </div>

      {/* 底部提交区 */}
      <div style={s.footer}>
        {error && <p style={s.errorText}>{error}</p>}
        <button
          style={s.submitBtn(!valid || loading)}
          onClick={handleSubmit}
          disabled={!valid || loading}
        >
          {loading ? '提交中…' : '下一步 →'}
        </button>
      </div>
    </div>
  )
}
