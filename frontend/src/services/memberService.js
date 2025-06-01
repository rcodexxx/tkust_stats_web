// frontend/src/services/memberService.js
import apiClient from './apiClient'; // 匯入您設定好的 Axios 實例

export default {
    /**
     * 獲取成員列表。
     * @param {boolean} fetchAll - 是否獲取所有成員 (包括非活躍的)，預設為 false (只獲取活躍成員，需與後端 API 參數對應)。
     * 根據之前的討論，後端 /api/members 接收 'all=true' 表示獲取所有。
     * 所以這裡 fetchAll=true => params: { all: true }
     * fetchAll=false => params: {} (後端預設可能只回傳活躍，或也用 all=false)
     * 這裡我們假設 fetchAll=true 意味著獲取所有，否則只獲取活躍的。
     * 需要與後端 GET /api/members 的參數邏輯對應。
     * 假設後端 API：?all=true -> 所有成員; ?all=false 或無此參數 -> 活躍成員
     */
    getAllMembers(fetchAll = false) {
        // 假設後端 API /members 接收 all=true 獲取所有，否則預設為活躍成員 (或根據 active_only)
        // 您需要根據後端 get_members_list 的實際參數來調整這裡的 params
        // 之前後端範例是 active_only_str = request.args.get('all', 'false', type=str).lower() == 'true'
        // 這意味著 ?all=true 會讓後端 active_only 變 false (獲取所有)
        // ?all=false 或不傳 all，會讓後端 active_only 變 true (只獲取活躍)
        // 所以 fetchAll=true => params: { all: 'true' }
        // fetchAll=false => params: { all: 'false' } (或者不傳，依賴後端預設)
        const params = {};
        if (fetchAll) {
            params.all = 'true'; // 獲取所有 (活躍+非活躍)
        } else {
            // 如果不傳 'all' 參數，後端應預設回傳活躍成員，或者您可以明確傳遞
            // params.all = 'false'; // 如果需要明確告知只獲取活躍的
        }
        return apiClient.get('/members', {params});
    },

    /**
     * 獲取單個成員的詳細資訊。
     * @param {number|string} memberId - 成員的 ID。
     */
    getMember(memberId) {
        return apiClient.get(`/members/${memberId}`);
    },

    /**
     * (管理員) 新增一個球隊成員及其關聯的 User 帳號。
     * @param {object} memberUserData - 包含 User 和 TeamMember 欄位的數據。
     * 例如：{ username: '...', password: '...', role: 'PLAYER', name: '...', display_name: '...', student_id: '...' }
     */
    createMemberWithUser(memberUserData) {
        return apiClient.post('/members', memberUserData); // 後端應為管理員新增成員的端點
    },

    /**
     * (管理員) 更新一個現有球隊成員的資訊。
     * @param {number|string} memberId - 要更新的成員 ID。
     * @param {object} memberData - 包含要更新的 TeamMember (和可能的 User email) 欄位的數據。
     */
    updateMember(memberId, memberData) {
        // 這個端點可能與 PUT /api/profile/me (使用者更新自己資料) 不同，
        // 這是管理員更新任何成員的。
        return apiClient.put(`/members/${memberId}`, memberData);
    },

    /**
     * (管理員) 刪除一個球隊成員及其關聯的 User 帳號。
     * @param {number|string} memberId - 要刪除的成員 ID。
     */
    deleteMember(memberId) {
        return apiClient.delete(`/members/${memberId}`);
    }

    // 您可以根據需要加入更多與成員相關的 API 請求函數，
    // 例如，如果使用者可以更新自己的 TeamMember profile (不同於管理員編輯)：
    // updateMyMemberProfile(memberProfileData) {
    //   return apiClient.put('/profile/me/member-details', memberProfileData); // 假設有這樣的端點
    // }
};