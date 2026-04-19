import { createRouter, createWebHistory } from "vue-router";

// 路由表：仅负责 URL <-> 页面组件的映射
// 说明：组件使用懒加载，避免首次加载包体过大
const routes = [
  {
    // 根路径统一跳转到 home，避免出现空白页/未知状态
    path: "/",
    redirect: { name: "home" }
  },
  {
    path: "/HomeView",
    name: "home",
    component: () => import("../views/HomeView.vue")
  },
  {
    path: "/HotView",
    name: "hot",
    component: () => import("../views/HotView.vue")
  },
  {
    path: "/DataView",
    name: "data",
    component: () => import("../views/DataView.vue")
  },
  {
    path: "/ArchView",
    name: "arch",
    component: () => import("../views/ArchView.vue")
  },
  {
    path: "/VisionView",
    name: "vision",
    component: () => import("../views/VisionView.vue")
  },
  {
    path: "/SettingsView",
    name: "settings",
    component: () => import("../views/SettingsView.vue")
  },
  {
    // 兜底：未匹配到的路径回到 home
    path: "/:pathMatch(.*)*",
    redirect: { name: "home" }
  }
];

export default createRouter({
  history: createWebHistory(),
  routes,
  // 路由切换时滚动到顶部，保持与原先切换 Tab 的体验一致
  scrollBehavior() {
    return { top: 0 };
  }
});
