import { useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import Confetti from 'react-confetti'
import CandidateCard, { type CandidateData } from '../components/CandidateCard'

// ─── Hackathon 保命 Mock 数据 ─────────────────────────────────
// 路演时后端宕机可无缝切换此数据，保证 Demo 不冷场
const MOCK_TOP3_DATA: CandidateData[] = [
  {
    user_id: 'mock-001',
    name: '张明远',
    grade: '大三',
    major: '数学与应用数学',
    match_score: 95,
    contact_info: 'WeChat: zhangy2024',
    summary: '建模思路清晰，擅长微分方程与优化模型，曾获全国数模二等奖，与你的编程能力形成完美互补。',
    radar: [
      { dimension: '建模', user: 6, candidate: 9 },
      { dimension: '编程', user: 8, candidate: 5 },
      { dimension: '写作', user: 5, candidate: 7 },
      { dimension: '分析', user: 7, candidate: 9 },
      { dimension: '协作', user: 8, candidate: 8 },
    ],
  },
  {
    user_id: 'mock-002',
    name: '李子晴',
    grade: '大二',
    major: '计算机科学与技术',
    match_score: 88,
    contact_info: 'WeChat: lzq_coding',
    summary: '熟练掌握 Python / MATLAB 全栈数据处理，代码风格严谨，愿意长期组队，是难得的实力型编程手。',
    radar: [
      { dimension: '建模', user: 6, candidate: 6 },
      { dimension: '编程', user: 8, candidate: 10 },
      { dimension: '写作', user: 5, candidate: 4 },
      { dimension: '分析', user: 7, candidate: 8 },
      { dimension: '协作', user: 8, candidate: 7 },
    ],
  },
  {
    user_id: 'mock-003',
    name: '王思远',
    grade: '大四',
    major: '统计学',
    match_score: 82,
    contact_info: 'email: wsy@example.com',
    summary: '论文撰写经验丰富，逻辑严密，曾参与 3 次数模竞赛，擅长数据可视化和结果解读。',
    radar: [
      { dimension: '建模', user: 6, candidate: 7 },
      { dimension: '编程', user: 8, candidate: 6 },
      { dimension: '写作', user: 5, candidate: 9 },
      { dimension: '分析', user: 7, candidate: 8 },
      { dimension: '协作', user: 8, candidate: 9 },
    ],
  },
]

// ─── 主组件 ──────────────────────────────────────────────────
export default function MatchResultPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const [showConfetti, setShowConfetti] = useState(true)
  const [windowSize, setWindowSize] = useState({
    width: window.innerWidth,
    height: window.innerHeight,
  })

  // 从路由 state 读取候选人数据，失败时使用 Mock
  const routeData = location.state?.top3 as CandidateData[] | undefined
  const candidates: CandidateData[] = (routeData && routeData.length > 0)
    ? routeData
    : MOCK_TOP3_DATA

  const hasRealData = !!(routeData && routeData.length > 0)

  useEffect(() => {
    const stopAt = setTimeout(() => setShowConfetti(false), 5000)
    const onResize = () =>
      setWindowSize({ width: window.innerWidth, height: window.innerHeight })
    window.addEventListener('resize', onResize)
    return () => {
      clearTimeout(stopAt)
      window.removeEventListener('resize', onResize)
    }
  }, [])

  // ── 空数据兜底 ──
  if (!candidates || candidates.length === 0) {
    return (
      <div style={s.fallback}>
        <div style={s.fallbackIcon}>🔍</div>
        <h2 style={s.fallbackTitle}>匹配已失效</h2>
        <p style={s.fallbackSub}>页面数据丢失，请重新完成测评</p>
        <button style={s.fallbackBtn} onClick={() => navigate('/onboarding')}>
          返回首页重测
        </button>
      </div>
    )
  }

  return (
    <div style={s.page}>
      {showConfetti && (
        <Confetti
          width={windowSize.width}
          height={windowSize.height}
          recycle={false}
          numberOfPieces={300}
          style={{ position: 'fixed', top: 0, left: 0, zIndex: 999 }}
        />
      )}

      {/* 顶部 */}
      <div style={s.header}>
        <div style={s.step}>Step 4 of 4</div>
        <h1 style={s.headerTitle}>🎉 已为你匹配最佳结果</h1>
        <p style={s.headerSub}>基于 AI 效用函数计算的 Top 3 搭子，等你来连线</p>
        {!hasRealData && (
          <div style={s.mockBanner}>📋 演示模式 — 展示 Mock 数据</div>
        )}
      </div>

      {/* 候选人卡片网格 */}
      <div style={s.grid}>
        {candidates.map((c, i) => (
          <CandidateCard key={c.user_id} candidate={c} rank={i} />
        ))}
      </div>

      {/* 底部重新测评 */}
      <div style={s.footer}>
        <button style={s.restartBtn} onClick={() => navigate('/onboarding')}>
          重新测评
        </button>
      </div>
    </div>
  )
}

// ─── 样式 ────────────────────────────────────────────────────
const s = {
  page: {
    minHeight: '100dvh',
    background: 'linear-gradient(160deg, #f0f4ff 0%, #fafafa 60%)',
    fontFamily: "'PingFang SC', 'Helvetica Neue', sans-serif",
    paddingBottom: 80,
  } as React.CSSProperties,

  header: {
    padding: '32px 20px 20px',
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

  headerTitle: { margin: '0 0 6px', fontSize: 22, fontWeight: 700 } as React.CSSProperties,
  headerSub: { margin: '0 0 0', fontSize: 13, opacity: 0.85 } as React.CSSProperties,

  mockBanner: {
    marginTop: 10,
    display: 'inline-block',
    background: 'rgba(255,255,255,0.2)',
    padding: '4px 12px',
    borderRadius: 20,
    fontSize: 12,
  } as React.CSSProperties,

  // CSS Grid: 1 col on mobile, 3 col on wider screens via minmax
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
    gap: 16,
    padding: '20px 16px',
  } as React.CSSProperties,

  footer: {
    padding: '0 16px 16px',
    textAlign: 'center' as const,
  } as React.CSSProperties,

  restartBtn: {
    padding: '12px 32px',
    borderRadius: 12,
    border: '1.5px solid #6366f1',
    background: '#fff',
    color: '#6366f1',
    fontSize: 14,
    fontWeight: 600,
    cursor: 'pointer',
  } as React.CSSProperties,

  // ── 空数据兜底页 ──
  fallback: {
    minHeight: '100dvh',
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 40,
    fontFamily: "'PingFang SC', sans-serif",
    background: '#f9fafb',
    textAlign: 'center' as const,
  } as React.CSSProperties,

  fallbackIcon: { fontSize: 64, marginBottom: 16 } as React.CSSProperties,
  fallbackTitle: { fontSize: 22, fontWeight: 700, color: '#111827', margin: '0 0 8px' } as React.CSSProperties,
  fallbackSub: { fontSize: 14, color: '#6b7280', margin: '0 0 24px' } as React.CSSProperties,

  fallbackBtn: {
    padding: '14px 36px',
    borderRadius: 14,
    border: 'none',
    background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
    color: '#fff',
    fontSize: 16,
    fontWeight: 700,
    cursor: 'pointer',
  } as React.CSSProperties,
}
