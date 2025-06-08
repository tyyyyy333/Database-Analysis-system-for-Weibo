// 全局变量
const API_BASE_URL = 'http://localhost:5000/api';

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

// 登录表单提交
loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    const rememberMe = document.getElementById('remember-me').checked;
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
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
            localStorage.setItem('token', data.token);
            if (rememberMe) {
                localStorage.setItem('username', username);
            }
            
            showNotification('登录成功', 'success');
            // 跳转到主页面
            window.location.href = 'dashboard.html';
        } else {
            throw new Error(data.message || '登录失败');
        }
    } catch (error) {
        console.error('登录错误:', error);
        showNotification(error.message, 'error');
    }
});

// 注册表单提交
registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const username = document.getElementById('register-username').value;
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    const confirmPassword = document.getElementById('register-confirm-password').value;
    
    // 验证密码
    if (password !== confirmPassword) {
        showNotification('两次输入的密码不一致', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/register`, {
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
            switchAuthBox('login');
            // 清空注册表单
            registerForm.reset();
        } else {
            throw new Error(data.message || '注册失败');
        }
    } catch (error) {
        console.error('注册错误:', error);
        showNotification(error.message, 'error');
    }
});

// 显示通知
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // 3秒后移除
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

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