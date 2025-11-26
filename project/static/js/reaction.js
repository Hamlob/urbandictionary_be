// reaction.js
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}
const csrftoken = getCookie('csrftoken');

document.addEventListener('click', async (e) => {
    const btn = e.target.closest('.reaction-button');
    if (!btn) return;

    const type = btn.dataset.type; // 'like' or 'dislike'
    const article = btn.closest('article.post-card');
    const postId = article.dataset.postId;
    const likeBtn = article.querySelector('.like-button');
    const dislikeBtn = article.querySelector('.dislike-button');
    const likeCountEl = article.querySelector('.like-count');
    const dislikeCountEl = article.querySelector('.dislike-count');

    btn.disabled = true;
    try {
        const resp = await fetch(`/posts/${postId}/react/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ type })
    });

    if (resp.redirected && resp.url.includes('/posts/login/')) {
        const go = confirm('Prosím prihláste sa, aby ste mohli reagovať na príspevok.');
        if (go) {
            window.location.href = resp.url;
        }
        return;
    }
    if (!resp.ok) {
        if (resp.status === 403) {
            alert('Prosím prihláste sa, aby ste mohli reagovať na príspevok.');
        } else if (resp.status === 503) {
            alert('Služba je momentálne nedostupná.');
        } else {
            alert('Nepodarilo sa aktualizovať reakciu.');
        }
        return;
    }

    const data = await resp.json();
    // Update UI from server truth
    const liked = data.state === 'like';
    const disliked = data.state === 'dislike';

    likeBtn.setAttribute('aria-pressed', liked ? 'true' : 'false');
    dislikeBtn.setAttribute('aria-pressed', disliked ? 'true' : 'false');

    likeBtn.querySelector('.reaction-label').textContent = liked ? 'Liked' : 'Like';
    dislikeBtn.querySelector('.reaction-label').textContent = disliked ? 'Disliked' : 'Dislike';

    likeCountEl.textContent = data.likes;
    dislikeCountEl.textContent = data.dislikes;
    }   
    catch (err) {
        console.error(err);
        alert('Network error.');
    }   
    finally {
        btn.disabled = false;
    }
});
