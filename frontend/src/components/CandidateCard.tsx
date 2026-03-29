import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  ResponsiveContainer,
  Tooltip,
} from 'recharts'

export interface RadarDim {
  dimension: string
  user: number
  candidate: number
}

export interface CandidateData {
  user_id: string
  name: string
  grade: string
  major: string
  match_score: number   // 0–100
  contact_info: string  // 邮箱
  summary: string
  radar: RadarDim[]
}

interface Props {
  readonly candidate: CandidateData
  readonly rank: number
}

// 头像颜色池（根据 rank 区分）
const AVATAR_COLORS = ['#6366f1', '#f97316', '#10b981']
const AVATAR_LABEL = ['#1', '#2', '#3']

export default function CandidateCard({ candidate, rank }: Props) {
  const avatarColor = AVATAR_COLORS[rank] ?? '#6366f1'

  let scoreColor: string
  if (candidate.match_score >= 90) scoreColor = '#10b981'
  else if (candidate.match_score >= 75) scoreColor = '#6366f1'
  else scoreColor = '#f97316'

  return (
    <div style={s.card}>
      {/* 排名徽章 */}
      <div style={{ ...s.rankBadge, background: avatarColor }}>
        {AVATAR_LABEL[rank]}
      </div>

      {/* 基础信息 */}
      <div style={s.topRow}>
        <div style={{ ...s.avatar, background: avatarColor }}>
          {candidate.name.charAt(0)}
        </div>
        <div style={s.info}>
          <div style={s.name}>{candidate.name}</div>
          <div style={s.meta}>{candidate.grade} · {candidate.major}</div>
        </div>
        <div style={{ ...s.score, color: scoreColor }}>
          <span style={s.scoreNum}>{candidate.match_score}</span>
          <span style={s.scorePct}>%</span>
        </div>
      </div>

      {/* 推荐摘要 */}
      <p style={s.summary}>{candidate.summary}</p>

      {/* 雷达图：双边形，蓝=你 橙=候选人 */}
      <div style={s.chartWrap}>
        <div style={s.chartLegend}>
          <span style={s.legendDot('#6366f1')} />{'\u00a0你'}
          <span style={{ ...s.legendDot('#f97316'), marginLeft: 12 }} />{'\u00a0'}{candidate.name}
        </div>
        <ResponsiveContainer width="100%" height={200}>
          <RadarChart data={candidate.radar} margin={{ top: 10, right: 20, bottom: 10, left: 20 }}>
            <PolarGrid stroke="#e5e7eb" />
            <PolarAngleAxis
              dataKey="dimension"
              tick={{ fontSize: 11, fill: '#6b7280' }}
            />
            <Tooltip
              formatter={(value, name) => [`${value ?? '-'} 分`, name === 'user' ? '你' : candidate.name]}
            />
            <Radar
              name="user"
              dataKey="user"
              stroke="#6366f1"
              fill="#6366f1"
              fillOpacity={0.25}
              strokeWidth={2}
            />
            <Radar
              name="candidate"
              dataKey="candidate"
              stroke="#f97316"
              fill="#f97316"
              fillOpacity={0.25}
              strokeWidth={2}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {/* CTA 按钮 */}
      <button
        style={s.ctaBtn(true, avatarColor)}
      >
        {`� ${candidate.contact_info}`}
      </button>
    </div>
  )
}

// ─── 样式 ────────────────────────────────────────────────────
const s = {
  card: {
    background: '#fff',
    borderRadius: 20,
    padding: 20,
    boxShadow: '0 4px 16px rgba(0,0,0,0.08)',
    position: 'relative' as const,
    overflow: 'hidden',
  } as React.CSSProperties,

  rankBadge: {
    position: 'absolute' as const,
    top: 0,
    right: 0,
    width: 36,
    height: 36,
    borderRadius: '0 20px 0 12px',
    color: '#fff',
    fontSize: 14,
    fontWeight: 700,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  } as React.CSSProperties,

  topRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
    marginBottom: 10,
  } as React.CSSProperties,

  avatar: {
    width: 46,
    height: 46,
    borderRadius: '50%',
    color: '#fff',
    fontSize: 20,
    fontWeight: 700,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  } as React.CSSProperties,

  info: { flex: 1 } as React.CSSProperties,
  name: { fontSize: 16, fontWeight: 700, color: '#111827' } as React.CSSProperties,
  meta: { fontSize: 12, color: '#6b7280', marginTop: 2 } as React.CSSProperties,

  score: {
    textAlign: 'right' as const,
    flexShrink: 0,
  } as React.CSSProperties,

  scoreNum: { fontSize: 28, fontWeight: 800, lineHeight: 1 } as React.CSSProperties,
  scorePct: { fontSize: 14, fontWeight: 600 } as React.CSSProperties,

  summary: {
    fontSize: 13,
    color: '#6b7280',
    lineHeight: 1.5,
    margin: '0 0 12px',
    padding: '8px 12px',
    background: '#f9fafb',
    borderRadius: 10,
  } as React.CSSProperties,

  chartWrap: { marginBottom: 14 } as React.CSSProperties,

  chartLegend: {
    fontSize: 12,
    color: '#6b7280',
    display: 'flex',
    alignItems: 'center',
    marginBottom: 4,
    paddingLeft: 4,
  } as React.CSSProperties,

  legendDot: (color: string) => ({
    display: 'inline-block',
    width: 10,
    height: 10,
    borderRadius: '50%',
    background: color,
    marginRight: 4,
  } as React.CSSProperties),

  ctaBtn: (revealed: boolean, color: string) => ({
    width: '100%',
    minHeight: 46,
    borderRadius: 12,
    border: revealed ? `1.5px solid ${color}` : 'none',
    background: revealed ? '#fff' : color,
    color: revealed ? color : '#fff',
    fontSize: 14,
    fontWeight: 700,
    cursor: revealed ? 'default' : 'pointer',
    transition: 'all 0.25s',
    letterSpacing: 0.3,
    padding: '0 16px',
    wordBreak: 'break-all' as const,
  } as React.CSSProperties),
}
