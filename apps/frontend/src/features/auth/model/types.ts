export interface RegisterRequest {
  email: string
  password: string
}

export interface RegisteredUser {
  id: string
  email: string
  created_at: string
}

export interface RegisterResponse {
  data: RegisteredUser
}
