/**
 * 종목 상세 페이지 JavaScript
 */
'use strict';

const API_BASE = '/api';
let chartInstance = null;

function scoreColor(s) {
  return s >= 60 ? 'score-color-high' : s >= 40 ? 'score-color-mid' : 'score-color-low';
}
function changeHtml(v) {
  if (v > 0) return `<span style="color:var(--positive)">+${v.toFixed(1)}</span>`;
  if (v < 0) return `<span style="color:var(--negative)">${v.toFixed(1)}</span>`;
  return `<span>${v.toFixed(1)}</span>`;
}
function toast(msg) {
  let el = document.querySelector('.toast');
  if (!el) { el = document.createElement('div'); el.className = 'toast'; document.body.appendChild(el); }
  el.textContent = msg; el.classList.add('show');
  setTimeout(() => el.classList.remove('show'), 2500);
}

async function loadDetail() {
  try {
    const res = await fetch(`${API_BASE}/stocks/${STOCK_CODE}`);
    const data = await res.json();

    document.getElementById('detailLoading').style.display  = 'none';
    document.getElementById('detailContent').style.display = 'block';
    document.getElementById('detailName').textContent = data.name;
    document.title = `${data.emoji} ${data.name} | 곡소리매매법`;

    document.getElementById('detailEmoji').textContent = data.emoji;
    document.getElementById('detailTitle').textContent = data.name;
    document.getElementById('detailCode').textContent  = `(${data.code})`;

    const scoreEl = document.getElementById('heroScore');
    scoreEl.textContent = `${data.score.toFixed(1)}점`;
    scoreEl.className = `hero-score-num ${scoreColor(data.score)}`;

    document.getElementById('dPos').textContent   = `${data.positive_count}개`;
    document.getElementById('dNeg').textContent   = `${data.negative_count}개`;
    document.getElementById('dNeu').textContent   = `${data.neutral_count}개`;
    document.getElementById('dTotal').textContent = `${data.total_count}개`;
    document.getElementById('dGrade').textContent = `${data.grade}등급`;
    document.getElementById('dChange').innerHTML  = changeHtml(data.score_change);

    // 댓글
    document.getElementById('detailCommentList').innerHTML =
      (data.comments || []).map(c => `
        <div class="comment-item ${c.sentiment}">
          <p style="font-size:0.88rem">${c.content}</p>
          <div class="comment-meta">${c.author} · 👍 ${c.likes} · ${c.source}</div>
        </div>`).join('');

    // DART 링크
    document.getElementById('detailDartLink').href =
      `https://dart.fss.or.kr/corp/searchCorp.do?firmName=${encodeURIComponent(data.name)}`;

    // 차트
    if (data.score_history) renderChart(data.score_history);

    // 공유 버튼
    document.getElementById('detailKakaoShare').addEventListener('click', async () => {
      const share = await fetch(`${API_BASE}/share/${STOCK_CODE}`).then(r => r.json());
      await navigator.clipboard.writeText(share.share_text);
      toast('📋 공유 텍스트가 복사되었습니다!');
    });
    document.getElementById('detailLinkCopy').addEventListener('click', () => {
      navigator.clipboard.writeText(location.href).then(() => toast('🔗 링크 복사 완료!'));
    });

  } catch (e) {
    document.getElementById('detailLoading').innerHTML =
      `<p style="color:var(--negative)">⚠️ 로딩 실패: ${e.message}</p>`;
  }
}

function renderChart(history) {
  const canvas = document.getElementById('detailChart');
  if (!canvas) return;
  if (chartInstance) chartInstance.destroy();

  const ctx = canvas.getContext('2d');
  const gradient = ctx.createLinearGradient(0, 0, 0, 260);
  gradient.addColorStop(0, 'rgba(79,142,247,0.35)');
  gradient.addColorStop(1, 'rgba(79,142,247,0)');

  chartInstance = new Chart(canvas, {
    type: 'line',
    data: {
      labels: history.map(h => h.date.slice(5)),
      datasets: [{
        label: '감성점수',
        data: history.map(h => h.score),
        borderColor: '#4f8ef7',
        backgroundColor: gradient,
        borderWidth: 2.5,
        pointRadius: 4,
        pointHoverRadius: 6,
        fill: true,
        tension: 0.4,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#1c2230', borderColor: '#3a4560', borderWidth: 1,
          callbacks: { label: ctx => `감성: ${ctx.parsed.y.toFixed(1)}점` },
        },
      },
      scales: {
        x: { grid: { color: '#2a3040' }, ticks: { color: '#8890a8', font: { size: 11 } } },
        y: {
          min: 0, max: 100,
          grid: { color: '#2a3040' },
          ticks: { color: '#8890a8', font: { size: 11 }, callback: v => `${v}점` },
        },
      },
    },
  });
}

document.addEventListener('DOMContentLoaded', loadDetail);
