import axios from 'axios';

const api = axios.create({ baseURL: '/api', withCredentials: true });

api.interceptors.response.use(
  r => r,
  e => { if (e.response?.status === 401) { window.location.hash = '#/login'; } return Promise.reject(e); }
);

export const login = (u, p) => api.post('/login', { username: u, password: p });
export const logout = () => api.post('/logout');
export const getMe = () => api.get('/me');
export const getDashboard = () => api.get('/dashboard');
export const getEvidence = (params) => api.get('/evidence', { params });
export const getEvidenceDetail = (id) => api.get('/evidence/' + id);
export const createEvidence = (d) => api.post('/evidence', d);
export const updateEvidence = (id, d) => api.put('/evidence/' + id, d);
export const deleteEvidence = (id) => api.delete('/evidence/' + id);
export const submitApproval = (id) => api.post('/evidence/' + id + '/submit-approval');
export const uploadAttachment = (id, file) => { const f = new FormData(); f.append('file', file); return api.post('/evidence/' + id + '/attachments', f); };
export const deleteAttachment = (id) => api.delete('/attachments/' + id);
export const getPendingApprovals = () => api.get('/approvals/pending');
export const reviewApproval = (id, r, c) => api.post('/approvals/' + id + '/review', { result: r, comment: c });
export const getAlerts = (params) => api.get('/alerts', { params });
export const dismissAlert = (id) => api.post('/alerts/' + id + '/dismiss');
export const checkAlerts = () => api.post('/alerts/check');
export const getCategories = (params) => api.get('/categories', { params });
export const getProjects = () => api.get('/projects');
export const createProject = (d) => api.post('/projects', d);
export const updateProject = (id, d) => api.put('/projects/' + id, d);
export const deleteProject = (id) => api.delete('/projects/' + id);
export const getUsers = () => api.get('/users');
export const createUser = (d) => api.post('/users', d);
export const updateUser = (id, d) => api.put('/users/' + id, d);
export const deleteUser = (id) => api.delete('/users/' + id);
export const getAlertRules = () => api.get('/alert-rules');
export const createAlertRule = (d) => api.post('/alert-rules', d);
export const updateAlertRule = (id, d) => api.put('/alert-rules/' + id, d);
export const deleteAlertRule = (id) => api.delete('/alert-rules/' + id);
export const exportEvidence = (params) => api.get('/export/evidence', { params, responseType: 'blob' });
export const exportSettlement = (params) => api.get('/export/settlement', { params, responseType: 'blob' });
export const llmExtract = (text) => api.post('/llm/extract', { text });
export const getProjectHome = () => api.get("/project-home");
export const getSettlementPackages = (params) => api.get("/settlement-packages", { params });
export const createSettlementPackage = (d) => api.post("/settlement-packages", d);
export const updateSettlementPackage = (id, d) => api.put("/settlement-packages/" + id, d);
export const deleteSettlementPackage = (id) => api.delete("/settlement-packages/" + id);
export const getSettlementPackageItems = (pid) => api.get("/settlement-packages/" + pid + "/items");
export const addSettlementPackageItem = (pid, d) => api.post("/settlement-packages/" + pid + "/items", d);
export const removeSettlementPackageItem = (pid, iid) => api.delete("/settlement-packages/" + pid + "/items/" + iid);
export const exportSettlementPackage = (pid) => api.get("/settlement-packages/" + pid + "/export", { responseType: "blob" });
export const globalSearch = (params) => api.get("/search", { params });
export const batchUploadEvidence = (formData) => api.post('/evidence/batch-upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
export const getSettings = () => api.get("/settings");
export const updateSettings = (d) => api.put("/settings", d);
export const getEvidenceLinks = (eid) => api.get("/evidence/" + eid + "/links");
export const addEvidenceLink = (eid, d) => api.post("/evidence/" + eid + "/links", d);
export const removeEvidenceLink = (eid, lid) => api.delete("/evidence/" + eid + "/links/" + lid);
export const suggestLinks = (eid) => api.get("/evidence/" + eid + "/suggest-links");
