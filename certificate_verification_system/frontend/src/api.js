import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8001'; // FastAPI backend

const api = axios.create({
    baseURL: API_BASE_URL,
});

// Interceptor to attach JWT token
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

export const login = async (username, password) => {
    const response = await api.post('/auth/login', { username, password });
    return response.data;
};

export const register = async (username, password, dbPath) => {
    const response = await api.post('/auth/register', { username, password, db_path: dbPath || '' });
    return response.data;
};

export const issueCertificate = async (studentName, degree, year) => {
    const response = await api.post('/api/issue', { student_name: studentName, degree, year });
    return response.data;
};

export const revokeCertificate = async (certId) => {
    const response = await api.post('/api/revoke', { cert_id: certId });
    return response.data;
};



export const getIssuers = async () => {
    const response = await api.get('/api/issuers');
    return response.data;
};

export const getHistory = async () => {
    const response = await api.get('/api/history');
    return response.data;
};

export const getBalance = async () => {
    const response = await api.get('/api/balance');
    return response.data;
};

export const browseFolder = async () => {
    const response = await api.get('/api/browse-folder');
    return response.data;
};

export const getSyncStatus = async () => {
    const response = await api.get('/api/sync-status');
    return response.data;
};

export const verifyCertificate = async (certId) => {
    const response = await api.post('/api/verify', { cert_id: certId });
    return response.data;
};

export default api;
