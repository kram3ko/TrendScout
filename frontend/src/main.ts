import { createPinia } from "pinia";
import { createApp } from "vue";

import App from "./App.vue";
import { router } from "./router";
import { initializeTheme } from "./shared/theme";
import "./styles.css";

initializeTheme();
createApp(App).use(createPinia()).use(router).mount("#app");
