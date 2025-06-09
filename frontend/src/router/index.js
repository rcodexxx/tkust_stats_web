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
import MatchManagementView from "@/views/MatchManagementView.vue";

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
        meta: {requiresAuth: true}
    },
    {
        path: '/match-records/create',
        name: 'RecordMatch',
        component: MatchRecordView,
        meta: {requiresAuth: true}
    },
    {
        path: '/matches/management',
        name: 'MatchManagement', // 新的路由名稱
        component: MatchManagementView,
        meta: {requiresAuth: true}
    },
    // --- 管理相關路由 ---
    {
        path: '/management',
        name: 'ManagementCenter',
        component: ManagementCenterView,
        meta: {requiresAuth: true}
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
