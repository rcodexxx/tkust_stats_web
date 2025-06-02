// frontend/src/services/memberService.js
import apiClient from './apiClient'; // 您設定好的 Axios 實例

const BASE_URL = '/members'; // API 端點的基礎路徑

export default {
    /**
     * 獲取成員列表。
     * @param {object} params - 可選的查詢參數, 例如 { all: true, name: 'search', sort_by: 'name', sort_order: 'asc' }
     */
    getAllMembers(params = {all: true}) { // 管理列表通常獲取所有
        return apiClient.get(BASE_URL, {params});
    },

    /**
     * 獲取單個成員的詳細資訊。
     * @param {number|string} memberId - 成員的 ID。
     */
    getMember(memberId) {
        return apiClient.get(`${BASE_URL}/${memberId}`);
    },

    /**
     * (管理員) 新增一個球隊成員及其關聯的 User 帳號。
     * @param {object} fullMemberData - 包含 User 和 Member 欄位的數據。
     * 例如：{
     * username: '0912345678', // User 的手機號 (必填)
     * name: '陳大文',         // Member 的真實姓名 (必填)
     * password: 'optionalPassword', // User 密碼 (可選，否則用手機號)
     * email: 'test@example.com',   // User email (可選)
     * role: 'PLAYER',              // User 角色 (可選，預設PLAYER)
     * display_name: '大文',        // Member 顯示名稱 (可選)
     * student_id: 'S1234567',     // Member 學號 (可選)
     * gender: 'MALE',              // Member 性別 (Enum NAME)
     * position: 'BACK',            // Member 位置 (Enum NAME)
     * organization_id: 1,        // Member 組織 ID
     * mu: 25.0, sigma: 8.333,    // Member TrueSkill
     * racket: 'Yonex XYZ',         // Member 球拍 (模型中是 racket)
     * join_date: '2024-01-01',     // Member 入隊日期 (YYYY-MM-DD)
     * is_active: true,             // Member 活躍狀態
     * is_active_user: true,        // User 帳號活躍狀態
     * notes: '一些備註'            // Member 備註
     * }
     */
    createMember(fullMemberData) {
        return apiClient.post(BASE_URL, fullMemberData);
    },

    /**
     * (管理員) 更新一個現有球隊成員的資訊，並可能創建/更新其 User 帳號。
     * @param {number|string} memberId - 要更新的成員 ID。
     * @param {object} updateData - 包含要更新的 Member 和 User 欄位的數據。
     * payload 結構與 createMember 類似，但只包含要修改的欄位。
     * 例如，若要自動創建 User，需提供 'username' (手機號)。
     */
    updateMember(memberId, updateData) {
        return apiClient.put(`${BASE_URL}/${memberId}`, updateData);
    },

    /**
     * (管理員) 刪除一個球隊成員及其關聯的 User 帳號。
     * @param {number|string} memberId - 要刪除的成員 ID。
     */
    deleteMember(memberId) {
        return apiClient.delete(`${BASE_URL}/${memberId}`);
    }
};