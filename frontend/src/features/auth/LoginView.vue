<script setup lang="ts">
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { ROUTE_DASHBOARD } from "@/router";
import { ApiError } from "@/shared/http";

import { useAuthStore } from "./store";

const auth = useAuthStore();
const router = useRouter();
const route = useRoute();

const username = ref("");
const password = ref("");
const error = ref("");
const pending = ref(false);

async function submit(): Promise<void> {
  pending.value = true;
  error.value = "";
  try {
    await auth.signIn({ username: username.value, password: password.value });
    const next = typeof route.query.next === "string" ? route.query.next : null;
    await router.push(next ?? { name: ROUTE_DASHBOARD });
  } catch (caught) {
    error.value = caught instanceof ApiError ? caught.message : "Could not reach the server";
  } finally {
    pending.value = false;
  }
}
</script>

<template>
  <form class="card login" @submit.prevent="submit">
    <div class="login__head">
      <h1>Trend<span>Scout</span></h1>
      <p class="muted">Sign in to review today's product shortlist.</p>
    </div>

    <label class="field">
      <span>Username</span>
      <input v-model="username" name="username" autocomplete="username" required />
    </label>

    <label class="field">
      <span>Password</span>
      <input
        v-model="password"
        name="password"
        type="password"
        autocomplete="current-password"
        required
      />
    </label>

    <p v-if="error" class="alert alert--error">{{ error }}</p>

    <button class="button" type="submit" :disabled="pending">
      {{ pending ? "Signing in…" : "Sign in" }}
    </button>
  </form>
</template>

<style scoped>
.login {
  display: grid;
  gap: 1.1rem;
  width: min(380px, 100%);
  padding: 2rem;
}

.login__head h1 {
  font-size: 1.5rem;
}

.login__head h1 span {
  color: var(--accent);
}

.login__head p {
  margin: 0.35rem 0 0;
  font-size: 0.9rem;
}
</style>
