import { createApp } from "vue";
import { createPinia } from "pinia";
import Particles from "@tsparticles/vue3";
import { loadSlim } from "@tsparticles/slim";
import App from "./App.vue";
import router from "./router";
import "./style.css";

const app = createApp(App);

// 全局状态管理
app.use(createPinia());

// 路由：用于 URL 与页面视图的映射（页面切换由 App.vue 内部的导航触发）
app.use(router);

// 背景粒子效果（保持现有初始化逻辑不变）
app.use(Particles, {
  init: async (engine) => {
    await loadSlim(engine);
  }
});

// 挂载根组件
app.mount("#app");

