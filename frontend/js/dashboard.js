// 状态管理
const state = {
    isBatchMode: false,
    selectedStars: new Set()
};

// 批量管理模式
function toggleBatchMode() {
    state.isBatchMode = !state.isBatchMode;
    const manageBtn = document.getElementById('manageBtn');
    const batchActions = document.getElementById('batchActions');
    
    if (state.isBatchMode) {
        manageBtn.innerHTML = '<i class="ri-close-line"></i>取消管理';
        manageBtn.classList.add('cancel');
        batchActions.classList.add('visible');
    } else {
        manageBtn.innerHTML = '<i class="ri-settings-4-line"></i>管理明星';
        manageBtn.classList.remove('cancel');
        batchActions.classList.remove('visible');
        state.selectedStars.clear();
    }
    
    document.querySelectorAll('.star-card').forEach(card => {
        const checkbox = card.querySelector('.checkbox');
        if (checkbox) {
            checkbox.classList.toggle('visible');
        }
        card.classList.remove('selected');
    });
    
    fetchAllStarsData();
}

// 明星选择
function toggleStarSelection(starId, event) {
    event.stopPropagation();
    const card = event.currentTarget;
    const checkbox = card.querySelector('.checkbox');
    
    if (state.selectedStars.has(starId)) {
        state.selectedStars.delete(starId);
        checkbox.classList.remove('checked');
        card.classList.remove('selected');
    } else {
        state.selectedStars.add(starId);
        checkbox.classList.add('checked');
        card.classList.add('selected');
    }
}

// 批量删除
async function deleteSelectedStars() {
    if (state.selectedStars.size === 0) {
        showMessage('请先选择要删除的明星', 'error');
        return;
    }

    if (!confirm(`确定要删除选中的 ${state.selectedStars.size} 个明星吗？`)) {
        return;
    }

    let successCount = 0;
    let failCount = 0;

    for (const starId of state.selectedStars) {
        try {
            const response = await fetch(`/api/stars/${starId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                successCount++;
            } else {
                failCount++;
            }
        } catch (error) {
            failCount++;
        }
    }

    if (successCount > 0) {
        showMessage(`成功删除 ${successCount} 个明星`, 'success');
    }
    if (failCount > 0) {
        showMessage(`删除失败 ${failCount} 个明星`, 'error');
    }

    state.selectedStars.clear();
    fetchAllStarsData();
    toggleBatchMode();
}

// 更新明星网格
function updateStarsGrid(stars) {
    const grid = document.getElementById('starsGrid');
    grid.innerHTML = `
        <div class="add-star-card" onclick="showAddStarModal()">
            <i class="ri-add-circle-line add-star-icon"></i>
            <div class="add-star-text">添加明星</div>
        </div>
        ${stars.map(star => `
            <div class="star-card ${state.selectedStars.has(star.id) ? 'selected' : ''}" 
                 onclick="${state.isBatchMode ? `toggleStarSelection(${star.id}, event)` : `window.location.href='/star/${star.id}'`}">
                <div class="checkbox ${state.isBatchMode ? 'visible' : ''} ${state.selectedStars.has(star.id) ? 'checked' : ''}"></div>
                <div class="star-card-header">
                    <div class="star-card-avatar">${star.name.charAt(0)}</div>
                    <div class="star-card-name">${star.name}</div>
                </div>
                <div class="star-card-metrics">
                    <div class="star-card-metric">
                        <div class="star-card-metric-value">${star.fans || 0}</div>
                        <div class="star-card-metric-label">粉丝数</div>
                    </div>
                    <div class="star-card-metric">
                        <div class="star-card-metric-value">${star.topics || 0}</div>
                        <div class="star-card-metric-label">话题数</div>
                    </div>
                    <div class="star-card-metric">
                        <div class="star-card-metric-value">${star.alert_count || 0}</div>
                        <div class="star-card-metric-label">预警数</div>
                    </div>
                    <div class="star-card-metric">
                        <div class="star-card-metric-value">${star.sentiment_score || 0}</div>
                        <div class="star-card-metric-label">情感得分</div>
                    </div>
                </div>
                <div class="star-card-status status-${star.status.toLowerCase()}">${star.status}</div>
            </div>
        `).join('')}
    `;
}

// 创建浮动球动画
function createFloatingBalls() {
    const container = document.getElementById('floatingBalls');
    const colors = ['rgba(255, 255, 255, 0.1)', 'rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.2)'];
    
    for (let i = 0; i < 15; i++) {
        const ball = document.createElement('div');
        ball.className = 'ball';
        
        const size = Math.random() * 100 + 50;
        ball.style.width = `${size}px`;
        ball.style.height = `${size}px`;
        ball.style.left = `${Math.random() * 100}%`;
        ball.style.top = `${Math.random() * 100}%`;
        ball.style.background = colors[Math.floor(Math.random() * colors.length)];
        ball.style.animationDelay = `${Math.random() * 5}s`;
        
        container.appendChild(ball);
    }
}

// 获取所有明星数据
async function fetchAllStarsData() {
    try {
        const response = await fetch('/api/stars');
        const stars = await response.json();
        updateStarsGrid(stars);
    } catch (error) {
        showMessage('获取明星列表失败：' + error.message, 'error');
    }
}

// 模态框控制
function showAddStarModal() {
    if (state.isBatchMode) return;
    const modal = document.getElementById('addStarModal');
    modal.style.display = 'flex';
}

function hideAddStarModal() {
    const modal = document.getElementById('addStarModal');
    modal.style.display = 'none';
    document.getElementById('addStarForm').reset();
}

// 添加明星
async function handleAddStar(event) {
    event.preventDefault();
    
    const formData = {
        name: document.getElementById('starName').value,
        weibo_url: document.getElementById('starUrl').value,
    };

    try {
        const response = await fetch('/api/stars', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        const data = await response.json();

        if (response.ok) {
            hideAddStarModal();
            fetchAllStarsData();
            showMessage('添加成功', 'success');
        } else {
            showMessage(data.error || '添加失败', 'error');
        }
    } catch (error) {
        showMessage('添加失败：' + error.message, 'error');
    }
}

// 消息提示
function showMessage(message, type = 'success') {
    alert(message); // 临时使用alert，后续可以改为更美观的提示
}

// 页面初始化
window.addEventListener('load', () => {
    createFloatingBalls();
    fetchAllStarsData();
});

// 导出函数供HTML使用
window.toggleBatchMode = toggleBatchMode;
window.toggleStarSelection = toggleStarSelection;
window.deleteSelectedStars = deleteSelectedStars;
window.showAddStarModal = showAddStarModal;
window.hideAddStarModal = hideAddStarModal;
window.handleAddStar = handleAddStar; 