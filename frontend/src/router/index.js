// src/router/index.js
import {createRouter, createWebHistory} from 'vue-router';

// 導入您的所有視圖組件
import LeaderboardView from '../views/LeaderboardView.vue';
import LoginView from "../views/LoginView.vue";
import RegisterView from "../views/RegisterView.vue";
import EditProfileView from "../views/EditProfileView.vue";
import ManagementCenterView from "@/views/Management/ManagementCenterView.vue";
import AddMemberView from "../views/Management/AddMemberView.vue";
import EditMemberView from "@/views/Management/EditMemberView.vue";
import MatchRecordView from "../views/MatchRecordView.vue";

const routes = [
    {
        path: '/',
        name: 'Leaderboard',
        component: LeaderboardView
        // 預設所有人都可以訪問
    },
    {
        path: '/login',
        name: 'Login',
        component: LoginView,
        meta: {guestOnly: true} // 標籤：只允許未登入使用者訪問
    },
    {
        path: '/register',
        name: 'Register',
        component: RegisterView,
        meta: {guestOnly: true} // 標籤：只允許未登入使用者訪問
    },
    {
        path: '/profile/edit',
        name: 'EditProfile',
        component: EditProfileView,
        meta: {requiresAuth: true} // 標籤：需要登入才能訪問
    },
    {
        path: '/match/record',
        name: 'RecordMatch',
        component: MatchRecordView,
        meta: {requiresAuth: true} // 標籤：需要登入才能訪問 (通常如此)
    },
    // --- 管理相關路由 ---
    {
        path: '/management',
        name: 'ManagementCenter',
        component: ManagementCenterView,
        meta: {requiresAuth: true} // 標籤：需要登入才能訪問
        // 您也可以加入更細的權限，例如 meta: { requiresAdmin: true }
    },
    {
        path: '/members/add',
        name: 'AddMember',
        component: AddMemberView,
        meta: {requiresAuth: true}
    },
    {
        path: '/members/edit/:id',
        name: 'EditMember',
        component: EditMemberView,
        props: true,
        meta: {requiresAuth: true}
    },
];

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes
});

export default router;
