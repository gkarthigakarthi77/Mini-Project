document.addEventListener('DOMContentLoaded', function() {
    // Dark mode toggle
    const toggle = document.getElementById('darkModeToggle');
    if (toggle) {
        const stored = localStorage.getItem('spa-theme');
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        const isDark = stored ? stored === 'dark' : prefersDark;
        if (isDark) {
            document.body.classList.add('dark-mode');
            document.body.classList.remove('light-mode');
        } else {
            document.body.classList.add('light-mode');
            document.body.classList.remove('dark-mode');
        }
        toggle.addEventListener('click', function(e) {
            e.preventDefault();
            const icon = toggle.querySelector('i');
            if (document.body.classList.contains('dark-mode')) {
                document.body.classList.remove('dark-mode');
                document.body.classList.add('light-mode');
                localStorage.setItem('spa-theme', 'light');
                icon.className = 'fas fa-sun';
            } else {
                document.body.classList.remove('light-mode');
                document.body.classList.add('dark-mode');
                localStorage.setItem('spa-theme', 'dark');
                icon.className = 'fas fa-moon';
            }
        });
        const icon = toggle.querySelector('i');
        if (document.body.classList.contains('dark-mode')) {
            icon.className = 'fas fa-moon';
        } else {
            icon.className = 'fas fa-sun';
        }
    }

    // Copy to clipboard
    document.querySelectorAll('.copy-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const targetId = this.dataset.copyTarget;
            const target = document.getElementById(targetId);
            if (target) {
                const text = target.value || target.textContent;
                if (text) {
                    navigator.clipboard.writeText(text).then(() => {
                        this.classList.add('copied');
                        this.innerHTML = '<i class="fas fa-check"></i>';
                        setTimeout(() => {
                            this.classList.remove('copied');
                            this.innerHTML = '<i class="fas fa-copy"></i>';
                        }, 2000);
                    }).catch(err => console.error('Copy failed', err));
                }
            }
        });
    });

    // FAQ icon rotation
    document.querySelectorAll('.faq-item .question').forEach(q => {
        q.addEventListener('click', function() {
            const icon = this.querySelector('i');
            if (icon) icon.classList.toggle('rotate-180');
        });
    });
});