// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化页面
    initializePage();
});

// 初始化页面
function initializePage() {
    // 这里可以添加页面初始化逻辑
    console.log('主页已加载');
}

// 添加卡片悬停效果
const cards = document.querySelectorAll('.card');
cards.forEach(card => {
    card.addEventListener('mouseenter', () => {
        card.style.transform = 'translateY(-5px)';
        card.style.boxShadow = '0 5px 15px rgba(255, 255, 255, 0.1)';
    });

    card.addEventListener('mouseleave', () => {
        card.style.transform = 'translateY(0)';
        card.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.1)';
    });
}); 