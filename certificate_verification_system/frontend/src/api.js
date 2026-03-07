import axios from 'axios';

const API_BASE_URL = 'http://localhost:8001'; // FastAPI backend

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

export default api;
