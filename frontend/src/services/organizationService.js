import apiClient from './apiClient'; // 匯入您設定好的 Axios 實例

const BASE_URL = '/organizations'; // API 端點的基礎路徑

export default {
    /**
     * 獲取組織列表。
     * @param {object} params - 可選的查詢參數，例如 { name: '搜尋詞' }
     * @returns {Promise} Axios Promise 物件
     */
    getOrganizations(params = {}) {
        return apiClient.get(BASE_URL, {params});
    },

    /**
     * 獲取單個組織的詳細資訊。
     * @param {number|string} id - 組織的 ID。
     * @returns {Promise} Axios Promise 物件
     */
    getOrganization(id) {
        return apiClient.get(`${BASE_URL}/${id}`);
    },

    /**
     * 新增一個組織。
     * @param {object} organizationData - 包含組織資訊的物件。
     * 例如：{ name: '新組織', short_name: '新簡稱', city: '台北', notes: '...' }
     * @returns {Promise} Axios Promise 物件
     */
    createOrganization(organizationData) {
        return apiClient.post(BASE_URL, organizationData);
    },

    /**
     * 更新一個現有組織的資訊。
     * @param {number|string} id - 要更新的組織 ID。
     * @param {object} organizationData - 包含要更新的組織欄位的物件。
     * @returns {Promise} Axios Promise 物件
     */
    updateOrganization(id, organizationData) {
        return apiClient.put(`${BASE_URL}/${id}`, organizationData);
    },

    /**
     * 刪除一個組織。
     * @param {number|string} id - 要刪除的組織 ID。
     * @returns {Promise} Axios Promise 物件
     */
    deleteOrganization(id) {
        return apiClient.delete(`${BASE_URL}/${id}`);
    }
};