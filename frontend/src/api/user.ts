const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

export interface UserBaseInfoPayload {
  name: string
  gender: string
  grade: string
  major: string
  competition_target: string
  want_long_term: boolean
  gender_preference?: string
  grade_preference?: string
  contact_info?: string
}

export interface UserCreateResponse {
  user_id: string
  name: string
  gender: string
  grade: string
  major: string
  competition_target: string
  want_long_term: boolean
  created_at: string
}

/** 提交用户基础信息，返回后端创建的用户记录（含 user_id）*/
export async function submitBaseInfo(data: UserBaseInfoPayload): Promise<UserCreateResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/users`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err?.detail ?? `请求失败 (${res.status})`)
  }
  return res.json()
}
