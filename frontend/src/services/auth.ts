import api from "./api";

export interface LoginData {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface UserResponse {
  id: number;
  email: string;
  username: string;
  is_active: boolean;
  created_at: string;
}

export async function loginApi(data: LoginData): Promise<TokenResponse> {
  const res = await api.post<TokenResponse>("/auth/login", data);
  return res.data;
}

export async function registerApi(data: RegisterData): Promise<UserResponse> {
  const res = await api.post<UserResponse>("/auth/register", data);
  return res.data;
}

export async function getMeApi(): Promise<UserResponse> {
  const res = await api.get<UserResponse>("/auth/me");
  return res.data;
}
