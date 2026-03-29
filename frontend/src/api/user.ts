const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''  // 空字符串 = 相对路径，走 Vite proxy 避免 CORS

export interface UserBaseInfoPayload {
  name: string
  gender: string
  grade: string
  major: string
  contact_info: string
  competition_target: string
  want_long_term: boolean
  gender_preference?: string
  grade_preference?: string
}

export interface UserCreateResponse {
  user_id: string
  session_id: string
  message: string
}

/** 提交用户基础信息，返回后端创建的用户记录（含 user_id + session_id）*/
export async function submitBaseInfo(data: UserBaseInfoPayload): Promise<UserCreateResponse> {
  // frontend 字段 competition_target 对应后端字段 team_goal
  const payload = { ...data, team_goal: data.competition_target }
  const res = await fetch(`${API_BASE_URL}/api/v1/users`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err?.detail ?? `请求失败 (${res.status})`)
  }
  return res.json()
}
