// static/js/like_button.js
document.addEventListener('DOMContentLoaded', function() {
    const csrfToken = getCookie('csrftoken');
    const likeButton = document.getElementById('likeButton');

    if (likeButton) {
        likeButton.addEventListener('click', function() {
            if (this.disabled) return;
            
            const postId = this.dataset.postId;
            const likeCount = this.querySelector('.like-count');
            const likeIcon = this.querySelector('.like-icon');

            fetch(`/like/${postId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/json',
                },
            })
            .then(response => response.json())
            .then(data => {
                if (data.likes_count !== undefined) {
                    likeCount.textContent = data.likes_count;
                    this.disabled = true;
                    likeIcon.textContent = '❤️‍🔥';
                }
            })
            .catch(error => console.error('Error:', error));
        });
    }
});

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}