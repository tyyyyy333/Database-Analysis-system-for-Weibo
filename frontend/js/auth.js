// 全局变量
const API_BASE_URL = 'http://localhost:5000/api';

// Token管理
const TokenManager = {
    getAccessToken() {
        return localStorage.getItem('access_token');
    },
    
    getRefreshToken() {
        return localStorage.getItem('refresh_token');
    },
    
    setTokens(accessToken, refreshToken) {
        localStorage.setItem('access_token', accessToken);
        localStorage.setItem('refresh_token', refreshToken);
    },
    
    clearTokens() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('username');
    },
    
    async refreshToken() {
        try {
            const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.getRefreshToken()}`
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.setTokens(data.access_token, data.refresh_token);
                return true;
            }
            return false;
        } catch (error) {
            console.error('Token刷新失败:', error);
            return false;
        }
    }
};

// 请求拦截器
async function fetchWithAuth(url, options = {}) {
    // 添加认证头
    const accessToken = TokenManager.getAccessToken();
    if (accessToken) {
        options.headers = {
            ...options.headers,
            'Authorization': `Bearer ${accessToken}`
        };
    }
    
    try {
        let response = await fetch(url, options);
        
        // 如果token过期，尝试刷新
        if (response.status === 401) {
            const refreshSuccess = await TokenManager.refreshToken();
            if (refreshSuccess) {
                // 使用新token重试请求
                options.headers['Authorization'] = `Bearer ${TokenManager.getAccessToken()}`;
                response = await fetch(url, options);
            } else {
                // 刷新失败，清除token并跳转到登录页
                TokenManager.clearTokens();
                window.location.href = '/login';
                return;
            }
        }
        
        return response;
    } catch (error) {
        console.error('请求失败:', error);
        throw error;
    }
}

// DOM元素
const loginBox = document.getElementById('login-box');
const registerBox = document.getElementById('register-box');
const showRegisterLink = document.getElementById('show-register');
const showLoginLink = document.getElementById('show-login');
const loginForm = document.getElementById('login-form');
const registerForm = document.getElementById('register-form');

// 光束效果和密码显示切换
const root = document.documentElement;
const eye = document.getElementById('eyeball');
const eyeRegister = document.getElementById('eyeball-register');
const eyeConfirm = document.getElementById('eyeball-confirm');
const beam = document.getElementById('beam');
const beamRegister = document.getElementById('beam-register');
const beamConfirm = document.getElementById('beam-confirm');
const passwordInput = document.getElementById('login-password');
const registerPasswordInput = document.getElementById('register-password');
const confirmPasswordInput = document.getElementById('register-confirm-password');

// 光束效果
function updateBeam(e, beamElement, inputElement) {
    let rect = inputElement.getBoundingClientRect();
    let mouseX = rect.right + (rect.width / 2); 
    let mouseY = rect.top + (rect.height / 2);
    let rad = Math.atan2(mouseX - e.pageX, mouseY - e.pageY);
    let degrees = (rad * (20 / Math.PI) * -1) - 350;
    beamElement.style.transform = `translateY(-50%) rotate(${degrees}deg)`;
}

root.addEventListener('mousemove', (e) => {
    if (passwordInput.type === 'text') {
        updateBeam(e, beam, passwordInput);
    }
    if (registerPasswordInput.type === 'text') {
        updateBeam(e, beamRegister, registerPasswordInput);
    }
    if (confirmPasswordInput.type === 'text') {
        updateBeam(e, beamConfirm, confirmPasswordInput);
    }
});

// 密码显示切换
function togglePasswordVisibility(eyeButton, passwordField, beamElement) {
    eyeButton.addEventListener('click', e => {
        e.preventDefault();
        passwordField.type = passwordField.type === 'password' ? 'text' : 'password';
        passwordField.focus();
    });
}

togglePasswordVisibility(eye, passwordInput, beam);
togglePasswordVisibility(eyeRegister, registerPasswordInput, beamRegister);
togglePasswordVisibility(eyeConfirm, confirmPasswordInput, beamConfirm);

// 切换登录/注册框
showRegisterLink.addEventListener('click', (e) => {
    e.preventDefault();
    loginBox.style.display = 'none';
    registerBox.style.display = 'block';
});

showLoginLink.addEventListener('click', (e) => {
    e.preventDefault();
    registerBox.style.display = 'none';
    loginBox.style.display = 'block';
});

// 表单验证函数
function validateLoginForm(username, password) {
    const errors = [];
    
    if (!username.trim()) {
        errors.push('用户名不能为空');
    }
    
    if (!password) {
        errors.push('密码不能为空');
    }
    
    return errors;
}

function validateRegisterForm(username, email, password) {
    const errors = [];
    
    if (!username.trim()) {
        errors.push('用户名不能为空');
    } else if (username.length < 3) {
        errors.push('用户名至少需要3个字符');
    }
    
    if (!email.trim()) {
        errors.push('邮箱不能为空');
    } else if (!email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) {
        errors.push('请输入有效的邮箱地址');
    }
    
    if (!password) {
        errors.push('密码不能为空');
    } else if (password.length < 6) {
        errors.push('密码至少需要6个字符');
    }
    
    return errors;
}

// 设置加载状态
function setLoading(form, isLoading) {
    const submitButton = form.querySelector('button[type="submit"]');
    submitButton.disabled = isLoading;
    submitButton.innerHTML = isLoading ? 
        '<span class="spinner"></span> 处理中...' : 
        submitButton.getAttribute('data-original-text') || '提交';
}

// 显示通知
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    // 添加关闭按钮
    const closeButton = document.createElement('span');
    closeButton.className = 'close-button';
    closeButton.innerHTML = '&times;';
    closeButton.onclick = () => notification.remove();
    notification.appendChild(closeButton);
    
    document.body.appendChild(notification);
    
    // 3秒后自动移除
    setTimeout(() => {
        notification.classList.add('fade-out');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// 请求超时处理
async function fetchWithTimeout(url, options, timeout = 5000) {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeout);
    
    try {
        const response = await fetch(url, {
            ...options,
            signal: controller.signal
        });
        clearTimeout(id);
        return response;
    } catch (error) {
        clearTimeout(id);
        throw error;
    }
}

// 登录表单提交
loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    const rememberMe = document.getElementById('remember-me').checked;
    
    // 验证输入
    const errors = validateLoginForm(username, password);
    if (errors.length > 0) {
        errors.forEach(error => showNotification(error, 'error'));
        return;
    }
    
    setLoading(loginForm, true);
    
    try {
        const response = await fetchWithTimeout(`${API_BASE_URL}/api/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username,
                password,
                remember_me: rememberMe
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // 保存token
            TokenManager.setTokens(data.access_token, data.refresh_token);
            
            // 保存用户信息
            if (data.user) {
                localStorage.setItem('user', JSON.stringify(data.user));
            }
            
            // 如果选择了"记住我"，保存用户名
            if (rememberMe) {
                localStorage.setItem('username', username);
            } else {
                localStorage.removeItem('username');
            }
            
            showNotification('登录成功', 'success');
            window.location.href = 'home.html';
        } else {
            showNotification(data.message || '登录失败', 'error');
        }
    } catch (error) {
        showNotification('登录请求失败，请稍后重试', 'error');
    } finally {
        setLoading(loginForm, false);
    }
});

// 注册表单提交
registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('register-username').value;
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    const confirmPassword = document.getElementById('register-confirm-password').value;

    // 验证表单
    const errors = validateRegisterForm(username, email, password);
    if (errors.length > 0) {
        showNotification(errors[0], 'error');
        return;
    }

    // 验证密码确认
    if (password !== confirmPassword) {
        showNotification('两次输入的密码不一致', 'error');
        return;
    }

    setLoading(registerForm, true);

    try {
        const response = await fetchWithTimeout(`${API_BASE_URL}/api/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username,
                email,
                password
            })
        });

        const data = await response.json();

        if (response.ok) {
            showNotification('注册成功，请登录', 'success');
            // 切换到登录框
            registerBox.style.display = 'none';
            loginBox.style.display = 'block';
        } else {
            showNotification(data.message || '注册失败', 'error');
        }
    } catch (error) {
        showNotification('注册请求失败，请稍后重试', 'error');
    } finally {
        setLoading(registerForm, false);
    }
});

// 登出功能
async function logout() {
    try {
        const response = await fetchWithAuth(`${API_BASE_URL}/api/logout`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();
        
        if (response.ok) {
            showNotification('登出成功', 'success');
            // 清除本地存储的用户信息
            localStorage.removeItem('token');
            // 重定向到登录页面
            window.location.href = '/index_home';
        } else {
            showNotification(data.message || '登出失败', 'error');
        }
    } catch (error) {
        console.error('登出失败:', error);
        showNotification('登出请求失败，请稍后重试', 'error');
    }
}

// 检查认证状态
async function checkAuth() {
    const accessToken = TokenManager.getAccessToken();
    if (!accessToken) {
        return false;
    }
    
    try {
        const response = await fetchWithAuth(`${API_BASE_URL}/auth/check`);
        return response.ok;
    } catch (error) {
        console.error('认证检查失败:', error);
        return false;
    }
}

// 导出函数
window.logout = logout;
window.checkAuth = checkAuth;
window.fetchWithAuth = fetchWithAuth;

// 保存按钮原始文本
document.addEventListener('DOMContentLoaded', () => {
    const loginButton = loginForm.querySelector('button[type="submit"]');
    const registerButton = registerForm.querySelector('button[type="submit"]');
    
    loginButton.setAttribute('data-original-text', loginButton.textContent);
    registerButton.setAttribute('data-original-text', registerButton.textContent);
});

// 检查是否已登录
function checkAuth() {
    const token = localStorage.getItem('token');
    if (token) {
        // 验证token
        fetch(`${API_BASE_URL}/auth/verify`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
        .then(response => {
            if (response.ok) {
                // token有效，跳转到主页面
                window.location.href = 'dashboard.html';
            } else {
                // token无效，清除token
                localStorage.removeItem('token');
            }
        })
        .catch(error => {
            console.error('验证token失败:', error);
            localStorage.removeItem('token');
        });
    }
}

// 页面加载时检查登录状态
document.addEventListener('DOMContentLoaded', checkAuth); 