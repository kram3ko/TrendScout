import { defineStore } from "pinia";
import { computed, ref } from "vue";

import { UnauthorizedError } from "@/shared/http";

import * as api from "./api";
import type { Credentials, User } from "./types";

export const useAuthStore = defineStore("auth", () => {
  const user = ref<User | null>(null);
  const resolved = ref(false);

  const isAuthenticated = computed(() => user.value !== null);

  async function signIn(credentials: Credentials): Promise<void> {
    user.value = await api.login(credentials);
    resolved.value = true;
  }

  async function signOut(): Promise<void> {
    await api.logout();
    user.value = null;
  }

  /** Runs once before the first guarded navigation: the session lives in a cookie
   * the page cannot read, so only the API can confirm it. */
  async function restore(): Promise<void> {
    if (resolved.value) return;
    try {
      user.value = await api.fetchCurrentUser();
    } catch (error) {
      if (!(error instanceof UnauthorizedError)) throw error;
      user.value = null;
    } finally {
      resolved.value = true;
    }
  }

  return { user, isAuthenticated, signIn, signOut, restore };
});
