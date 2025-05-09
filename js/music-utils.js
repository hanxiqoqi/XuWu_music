function parseLrc(lrcText) {
    console.log('原始 LRC 文本:', lrcText);
    const lines = lrcText.split('\n');
    const lyrics = [];
    lines.forEach(line => {
        const match = line.match(/^\[(\d{2}):(\d{2})\.(\d{2,3})\](.*)$/);
        if (match) {
            const minutes = parseInt(match[1]);
            const seconds = parseInt(match[2]);
            const milliseconds = parseInt(match[3]);
            const time = minutes * 60 + seconds + milliseconds / 1000;
            const text = match[4];
            lyrics.push({ time, text });
        }
    });
    console.log('解析后的歌词:', lyrics);
    return lyrics;
}

function highlightLyric(lyrics, currentTime, lyricsDiv) {
    lyrics.forEach((lyric, index) => {
        const p = lyricsDiv.children[index];
        if (p) {
            if (lyric.time <= currentTime && (index === lyrics.length - 1 || lyrics[index + 1].time > currentTime)) {
                p.classList.add('highlight');
            } else {
                p.classList.remove('highlight');
            }
        }
    });
}

export { parseLrc, highlightLyric };


export function favoriteMusic(musicId) {
    fetch('/favorite_music', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: `music_id=${musicId}`
    })
   .then(response => {
        if (!response.ok) {
            throw new Error('收藏失败');
        }
        return response.json();
    })
   .then(data => {
        if (data.status === 'success') {
            alert('收藏成功');
        }
    })
   .catch(error => {
        console.error(error);
        alert('收藏失败，请稍后重试');
    });
}

export function showCommentAndRate(musicId) {
    const commentDiv = document.getElementById(`comment-and-rate-${musicId}`);
    commentDiv.style.display = 'block';
}

export function submitCommentAndRate(musicId) {
    const comment = document.getElementById(`comment-${musicId}`).value;
    const rating = document.getElementById(`rating-${musicId}`).value;
    fetch('/comment_and_rate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: `music_id=${musicId}&comment=${comment}&rating=${rating}`
    })
   .then(response => {
        if (!response.ok) {
            throw new Error('提交失败');
        }
        return response.json();
    })
   .then(data => {
        if (data.status === 'success') {
            alert('评论和评分提交成功');
            const commentDiv = document.getElementById(`comment-and-rate-${musicId}`);
            commentDiv.style.display = 'none';
        }
    })
   .catch(error => {
        console.error(error);
        alert('提交失败，请稍后重试');
    });
}