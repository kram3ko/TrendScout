<script setup lang="ts">
import { useRouter } from "vue-router";

import { useAuthStore } from "@/features/auth/store";
import { ROUTE_DASHBOARD, ROUTE_LOGIN, ROUTE_SALES_BOOST } from "@/router";
import ThemeToggle from "@/shared/ThemeToggle.vue";

const auth = useAuthStore();
const router = useRouter();

async function signOut(): Promise<void> {
  await auth.signOut();
  await router.push({ name: ROUTE_LOGIN });
}
</script>

<template>
  <header v-if="auth.isAuthenticated" class="topbar">
    <div class="topbar__inner">
      <RouterLink :to="{ name: ROUTE_DASHBOARD }" class="brand">
        Trend<span>Scout</span>
      </RouterLink>
      <nav class="nav">
        <RouterLink :to="{ name: ROUTE_DASHBOARD }">Dashboard</RouterLink>
        <RouterLink :to="{ name: ROUTE_SALES_BOOST }">Sales Boost</RouterLink>
      </nav>
      <div class="account">
        <ThemeToggle />
        <span class="muted">{{ auth.user?.username }}</span>
        <button type="button" class="button button--ghost" @click="signOut">Sign out</button>
      </div>
    </div>
  </header>

  <div v-else class="theme-floating">
    <ThemeToggle />
  </div>

  <main :class="auth.isAuthenticated ? 'page' : 'page page--bare'">
    <RouterView />
  </main>
</template>

<style scoped>
.topbar {
  position: sticky;
  top: 0;
  z-index: 10;
  background: color-mix(in srgb, var(--surface) 85%, transparent);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid var(--border);
}

.topbar__inner {
  display: flex;
  align-items: center;
  gap: 2rem;
  max-width: 1240px;
  margin: 0 auto;
  padding: 0.85rem 1.5rem;
}

.brand {
  font-size: 1.05rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--text);
}

.brand span {
  color: var(--accent);
}

.nav {
  display: flex;
  gap: 0.35rem;
  margin-right: auto;
}

.nav a {
  padding: 0.4rem 0.75rem;
  border-radius: var(--radius-sm);
  color: var(--text-muted);
  font-weight: 550;
}

.nav a.router-link-active {
  background: var(--surface-muted);
  color: var(--text);
}

.account {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.theme-floating {
  position: fixed;
  top: 1rem;
  right: 1rem;
  z-index: 10;
}

.page {
  max-width: 1240px;
  margin: 0 auto;
  padding: 1.75rem 1.5rem 4rem;
}

.page--bare {
  display: grid;
  place-items: center;
  min-height: 100dvh;
  padding: 1.5rem;
}

@media (max-width: 640px) {
  .topbar__inner {
    flex-wrap: wrap;
    gap: 0.75rem;
  }

  .nav {
    order: 3;
    width: 100%;
  }

  .account .muted {
    display: none;
  }
}
</style>
