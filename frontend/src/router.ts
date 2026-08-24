import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";

import { useAuthStore } from "@/features/auth/store";

export const ROUTE_LOGIN = "login";
export const ROUTE_DASHBOARD = "dashboard";
export const ROUTE_SALES_BOOST = "sales-boost";

const routes: RouteRecordRaw[] = [
  {
    path: "/login",
    name: ROUTE_LOGIN,
    component: () => import("@/features/auth/LoginView.vue"),
    meta: { public: true },
  },
  {
    path: "/",
    name: ROUTE_DASHBOARD,
    component: () => import("@/features/products/DashboardView.vue"),
  },
  {
    path: "/sales-boost",
    name: ROUTE_SALES_BOOST,
    component: () => import("@/features/salesboost/SalesBoostView.vue"),
  },
  { path: "/:pathMatch(.*)*", redirect: { name: ROUTE_DASHBOARD } },
];

export const router = createRouter({ history: createWebHistory(), routes });

router.beforeEach(async (to) => {
  const auth = useAuthStore();
  await auth.restore();

  if (!to.meta.public && !auth.isAuthenticated) {
    return { name: ROUTE_LOGIN, query: { next: to.fullPath } };
  }
  if (to.meta.public && auth.isAuthenticated) {
    return { name: ROUTE_DASHBOARD };
  }
  return true;
});
