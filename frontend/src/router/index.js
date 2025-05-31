// src/router/index.js
import {createRouter, createWebHistory} from 'vue-router';
import LeaderboardView from '../views/LeaderboardView.vue';
import AddMemberView from "../views/AddMemberView.vue";
import MatchRecordView from "../views/MatchRecordView.vue";
import LoginView from "../views/LoginView.vue";
import RegisterView from "../views/RegisterView.vue";
import EditProfileView from "../views/EditProfileView.vue";

const routes = [
    {path: '/', name: 'Leaderboard', component: LeaderboardView},
    {
        path: '/login',
        name: 'Login',
        component: LoginView,
        meta: {guestOnly: true} // 只允許未登入使用者訪問
    },
    {
        path: '/register',
        name: 'Register',
        component: RegisterView,
        meta: {guestOnly: true} // 只允許未登入使用者訪問
    }, {
        path: '/', name: 'Leaderboard', component: LeaderboardView
    }, {
        path: '/members/add', name: 'AddMember', component: AddMemberView
    }, {
        path: '/match/record', name: 'RecordMatch', component: MatchRecordView
    }, {
        path: '/profile/edit', name: 'EditProfile', component: EditProfileView
    }]

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL), routes
})

export default router