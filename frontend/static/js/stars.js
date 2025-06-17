// 连接WebSocket
const socket = io();

// 监听数据分析完成事件
socket.on('analysis_complete', function(data) {
    if (data.status === 'success') {
        // 更新明星数据
        updateStarData(data.celebrity_id);
        // 显示成功消息
        showMessage('数据分析完成', 'success');
    } else {
        // 显示错误消息
        showMessage(data.message || '数据分析失败', 'error');
    }
});

// 更新明星数据
async function updateStarData(celebrityId) {
    try {
        const response = await fetch(`/api/stars/${celebrityId}`);
        const starData = await response.json();
        
        // 更新表格中的明星数据
        const starRow = document.querySelector(`tr[data-star-id="${celebrityId}"]`);
        if (starRow) {
            starRow.querySelector('td:nth-child(3)').textContent = starData.status;
            starRow.querySelector('td:nth-child(4)').textContent = starData.fans;
            starRow.querySelector('td:nth-child(5)').textContent = starData.topics;
            starRow.querySelector('td:nth-child(6)').textContent = starData.alert_count;
            starRow.querySelector('td:nth-child(7)').textContent = starData.sentiment_score;
        }
        
        // 如果当前正在查看该明星的详情页，也更新详情页数据
        if (window.location.pathname === `/star/${celebrityId}`) {
            updateStarDetail(starData);
        }
    } catch (error) {
        console.error('更新明星数据失败:', error);
        showMessage('更新数据失败，请刷新页面', 'error');
    }
}

// 更新明星详情页
function updateStarDetail(starData) {
    // 更新热度图表
    if (starData.heat_data) {
        updateHeatChart(starData.heat_data);
    }
    
    // 更新情感分析图表
    if (starData.sentiment_data) {
        updateSentimentChart(starData.sentiment_data);
    }
    
    // 更新黑粉分析图表
    if (starData.black_fan_data) {
        updateBlackFanChart(starData.black_fan_data);
    }
    
    // 更新粉丝分析图表
    if (starData.fan_data) {
        updateFanChart(starData.fan_data);
    }
}

// 添加明星
async function addStar(event) {
    event.preventDefault();
    
    const name = document.getElementById('starName').value;
    const url = document.getElementById('starUrl').value;
    const userId = document.getElementById('userId').value;
    
    try {
        const response = await fetch('/api/stars', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: name,
                url: url,
                user_id: userId
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showMessage('明星添加成功，开始爬取数据', 'success');
            // 清空表单
            document.getElementById('starName').value = '';
            document.getElementById('starUrl').value = '';
            // 重新加载明星列表
            await loadStars();
        } else {
            showMessage(data.error || '添加失败', 'error');
        }
    } catch (error) {
        console.error('添加明星失败:', error);
        showMessage('添加失败，请稍后重试', 'error');
    }
}

// 删除明星
async function deleteStar(starId) {
    if (!confirm('确定要删除该明星及其所有相关数据吗？此操作不可恢复！')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/stars/${starId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // 删除成功，更新界面
            const starRow = document.querySelector(`tr[data-star-id="${starId}"]`);
            if (starRow) {
                starRow.remove();
            }
            
            // 更新明星列表
            await loadStars();
            
            // 显示成功消息
            showMessage('删除成功', 'success');
        } else {
            // 显示错误消息
            showMessage(data.error || '删除失败', 'error');
        }
    } catch (error) {
        console.error('删除明星失败:', error);
        showMessage('删除失败，请稍后重试', 'error');
    }
}

// 显示消息提示
function showMessage(message, type = 'info') {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.textContent = message;
    
    // 添加到页面
    document.body.appendChild(messageDiv);
    
    // 3秒后自动消失
    setTimeout(() => {
        messageDiv.remove();
    }, 3000);
}

// 加载明星列表
async function loadStars() {
    try {
        const response = await fetch('/api/stars');
        const stars = await response.json();
        
        const tbody = document.querySelector('#starsTable tbody');
        tbody.innerHTML = '';
        
        stars.forEach(star => {
            const tr = document.createElement('tr');
            tr.setAttribute('data-star-id', star.id);
            tr.innerHTML = `
                <td>${star.name}</td>
                <td>${star.url}</td>
                <td>${star.status}</td>
                <td>${star.fans}</td>
                <td>${star.topics}</td>
                <td>${star.alert_count}</td>
                <td>${star.sentiment_score}</td>
                <td>
                    <button onclick="deleteStar(${star.id})" class="delete-btn">删除</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error('加载明星列表失败:', error);
        showMessage('加载明星列表失败，请刷新页面重试', 'error');
    }
} 