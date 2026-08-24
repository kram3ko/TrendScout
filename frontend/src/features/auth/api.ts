import { postJson, request } from "@/shared/http";

import type { Credentials, User } from "./types";

export const login = (credentials: Credentials): Promise<User> =>
  postJson<User>("/auth/login", credentials);

export const logout = (): Promise<void> => request<void>("/auth/logout", { method: "POST" });

export const fetchCurrentUser = (): Promise<User> => request<User>("/auth/me");
