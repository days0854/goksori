/**
 * 곡소리 매매법 - 메인 JavaScript
 * 기능: 종목 목록 로딩, 모달, 차트, 카카오 공유, 링크 복사
 */

'use strict';

// ── 상태 관리 ──────────────────────────────────────────────────────────────
const State = {
  currentPage: 1,
  pageSize: 50,
  sort: 'score_desc',
  search: '',
  totalStocks: 0,
  allStocks: [],
  currentStock: null,
  chartInstance: null,
};

// ── API ────────────────────────────────────────────────────────────────────
const API = {
  base: '/api',

  async getStocks(page = 1, size = 50, sort = 'score_desc', search = '') {
    const params = new URLSearchParams({ page, size, sort });
    if (search) params.append('search', search);
    const res = await fetch(`${API.base}/stocks/?${params}`);
    if (!res.ok) throw new Error('종목 데이터 로딩 실패');
    return res.json();
  },

  async getStockDetail(code) {
    const res = await fetch(`${API.base}/stocks/${code}`);
    if (!res.ok) throw new Error('종목 상세 로딩 실패');
    return res.json();
  },

  async getShareData(code) {
    const res = await fetch(`${API.base}/share/${code}`);
    if (!res.ok) throw new Error('공유 데이터 로딩 실패');
    return res.json();
  },

  async getScoreHistory(code, days = 30) {
    const res = await fetch(`${API.base}/sentiment/${code}/history?days=${days}`);
    if (!res.ok) throw new Error('히스토리 로딩 실패');
    return res.json();
  },
};

// ── 유틸 ──────────────────────────────────────────────────────────────────
const Utils = {
  scoreColor(score) {
    if (score >= 60) return 'score-color-high';
    if (score >= 40) return 'score-color-mid';
    return 'score-color-low';
  },

  barColor(score) {
    if (score >= 60) return 'bar-color-high';
    if (score >= 40) return 'bar-color-mid';
    return 'bar-color-low';
  },

  trendLabel(trend) {
    const map = { up: '📈 상승', down: '📉 하락', neutral: '➡️ 중립' };
    return map[trend] || trend;
  },

  trendClass(trend) {
    const map = { up: 'trend-up', down: 'trend-down', neutral: 'trend-neutral' };
    return map[trend] || 'trend-neutral';
  },

  changeText(change) {
    if (change > 0) return `<span class="change-pos">+${change.toFixed(1)}</span>`;
    if (change < 0) return `<span class="change-neg">${change.toFixed(1)}</span>`;
    return `<span>${change.toFixed(1)}</span>`;
  },

  formatTime(iso) {
    try {
      const d = new Date(iso);
      return `${d.getHours().toString().padStart(2,'0')}:${d.getMinutes().toString().padStart(2,'0')}`;
    } catch { return '-'; }
  },

  nextUpdateTime() {
    const now = new Date();
    const nextHour = Math.ceil(now.getHours() / 4) * 4;
    const next = new Date(now);
    next.setHours(nextHour, 0, 0, 0);
    if (next <= now) next.setHours(next.getHours() + 4);
    const diff = Math.round((next - now) / 60000);
    const h = Math.floor(diff / 60);
    const m = diff % 60;
    return h > 0 ? `${h}시간 ${m}분 후` : `${m}분 후`;
  },

  toast(msg) {
    let el = document.querySelector('.toast');
    if (!el) {
      el = document.createElement('div');
      el.className = 'toast';
      document.body.appendChild(el);
    }
    el.textContent = msg;
    el.classList.add('show');
    setTimeout(() => el.classList.remove('show'), 2500);
  },
};

// ── 렌더링 ──────────────────────────────────────────────────────────────────
const Render = {
  stockRow(stock, rank) {
    const scoreClass = Utils.scoreColor(stock.score);
    const barClass   = Utils.barColor(stock.score);
    const trendClass = Utils.trendClass(stock.trend);
    const rankClass  = rank <= 3 ? `rank-${rank}` : '';

    return `
    <div class="stock-row ${rankClass}" data-code="${stock.code}" data-name="${stock.name}">
      <!-- 종목 정보 -->
      <div class="col-stock">
        <span class="rank-badge">${rank}</span>
        <span class="stock-emoji">${stock.emoji}</span>
        <div class="stock-info">
          <span class="stock-name">${stock.name}</span>
          <span class="stock-code">${stock.code}</span>
        </div>
      </div>

      <!-- 감성 점수 -->
      <div class="col-score">
        <span class="score-num ${scoreClass}">${stock.score.toFixed(1)}점</span>
        <div class="score-bar-wrap">
          <div class="score-bar-fill ${barClass}" style="width:${stock.score}%"></div>
        </div>
      </div>

      <!-- 추세 / 등급 -->
      <div class="col-trend">
        <span class="trend-badge ${trendClass}">${Utils.trendLabel(stock.trend)}</span>
        <span class="grade-badge grade-${stock.grade}">${stock.grade}</span>
        ${Utils.changeText(stock.score_change)}
      </div>

      <!-- 공유 -->
      <div class="col-share">
        <button class="share-mini-btn" data-code="${stock.code}" data-name="${stock.name}"
                onclick="event.stopPropagation(); KakaoShare.shareStock('${stock.code}')">
          💬 공유
        </button>
      </div>
    </div>`;
  },

  stockGrid(stocks) {
    const grid = document.getElementById('stockGrid');
    if (!stocks.length) {
      grid.innerHTML = '<div class="loading-state"><p>검색 결과가 없습니다</p></div>';
    } else {
      grid.innerHTML = stocks
        .map((s, i) => Render.stockRow(s, (State.currentPage - 1) * State.pageSize + i + 1))
        .join('');
    }

    // 이벤트 바인딩
    grid.querySelectorAll('.stock-row').forEach(row => {
      row.addEventListener('click', () => Modal.open(row.dataset.code, row.dataset.name));
    });
  },

  statsBar(stocks, total) {
    const hot  = stocks.filter(s => s.score >= 70).length;
    const cold = stocks.filter(s => s.score <= 30).length;
    const avg  = stocks.length
      ? (stocks.reduce((a, s) => a + s.score, 0) / stocks.length).toFixed(1)
      : '-';

    document.getElementById('statTotal').textContent = total;
    document.getElementById('statHot').textContent   = `${hot}개`;
    document.getElementById('statCold').textContent  = `${cold}개`;
    document.getElementById('statAvg').textContent   = `${avg}점`;
    document.getElementById('statNextUpdate').textContent = Utils.nextUpdateTime();
    document.getElementById('lastUpdate').textContent =
      `${new Date().toLocaleTimeString('ko-KR', {hour:'2-digit', minute:'2-digit'})} 업데이트`;
  },

  pagination(total, page, size) {
    const totalPages = Math.ceil(total / size);
    const pag = document.getElementById('pagination');
    const info = document.getElementById('pageInfo');

    if (totalPages <= 1) { pag.style.display = 'none'; return; }
    pag.style.display = 'flex';
    info.textContent = `${page} / ${totalPages} 페이지`;
    document.getElementById('btnPrev').disabled = page <= 1;
    document.getElementById('btnNext').disabled = page >= totalPages;
  },
};

// ── 데이터 로딩 ────────────────────────────────────────────────────────────
async function loadStocks() {
  document.getElementById('loadingState').style.display = 'flex';
  document.getElementById('stockGrid').style.display = 'none';

  try {
    const data = await API.getStocks(
      State.currentPage, State.pageSize, State.sort, State.search
    );

    State.totalStocks = data.total;
    State.allStocks   = data.stocks;

    Render.stockGrid(data.stocks);
    Render.statsBar(data.stocks, data.total);
    Render.pagination(data.total, State.currentPage, State.pageSize);

    document.getElementById('loadingState').style.display = 'none';
    document.getElementById('stockGrid').style.display    = 'flex';

  } catch (err) {
    document.getElementById('loadingState').innerHTML =
      `<p style="color:var(--negative)">⚠️ 데이터 로딩 실패: ${err.message}</p>`;
    console.error(err);
  }
}

// ── 모달 ──────────────────────────────────────────────────────────────────
const Modal = {
  el: null,

  init() {
    this.el = document.getElementById('stockModal');
    document.getElementById('modalClose').addEventListener('click', () => this.close());
    document.getElementById('modalBackdrop').addEventListener('click', () => this.close());
    document.addEventListener('keydown', e => { if (e.key === 'Escape') this.close(); });

    // 탭 전환
    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        btn.classList.add('active');
        const tabId = `tab-${btn.dataset.tab}`;
        document.getElementById(tabId).classList.add('active');

        if (btn.dataset.tab === 'chart' && State.currentStock) {
          ChartModule.renderScoreChart(State.currentStock.code);
        }
      });
    });

    // 모달 공유 버튼
    document.getElementById('modalKakaoShare').addEventListener('click', () => {
      if (State.currentStock) KakaoShare.shareStock(State.currentStock.code);
    });
    document.getElementById('modalLinkShare').addEventListener('click', () => {
      if (State.currentStock) {
        const url = `${location.origin}/stock/${State.currentStock.code}`;
        navigator.clipboard.writeText(url).then(() => Utils.toast('🔗 링크가 복사되었습니다!'));
      }
    });
    document.getElementById('modalNaverLink').addEventListener('click', () => {
      if (State.currentStock) {
        window.open(
          `https://finance.naver.com/item/board.naver?code=${State.currentStock.code}`,
          '_blank'
        );
      }
    });
  },

  async open(code, name) {
    this.el.classList.add('open');
    this.el.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';

    // 로딩 상태 초기화
    document.getElementById('modalName').textContent  = name || code;
    document.getElementById('modalCode').textContent  = code;
    document.getElementById('modalEmoji').textContent = '⏳';
    document.getElementById('modalScore').textContent = '-';

    // 탭 초기화 (개요로)
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    document.querySelector('.tab-btn[data-tab="overview"]').classList.add('active');
    document.getElementById('tab-overview').classList.add('active');

    try {
      const data = await API.getStockDetail(code);
      State.currentStock = data;
      this.populate(data);
    } catch (err) {
      console.error(err);
      Utils.toast('종목 상세 로딩 실패');
    }
  },

  populate(data) {
    // 헤더
    document.getElementById('modalEmoji').textContent = data.emoji;
    document.getElementById('modalName').textContent  = data.name;
    document.getElementById('modalCode').textContent  = `(${data.code})`;

    // 점수 (색상)
    const scoreEl = document.getElementById('modalScore');
    scoreEl.textContent = `${data.score.toFixed(1)}점`;
    scoreEl.className = `score-big ${Utils.scoreColor(data.score)}`;

    // 개요 통계
    document.getElementById('modalGrade').textContent = `${data.grade}등급`;
    document.getElementById('modalPos').textContent   = `${data.positive_count}개`;
    document.getElementById('modalNeg').textContent   = `${data.negative_count}개`;
    document.getElementById('modalNeu').textContent   = `${data.neutral_count}개`;
    document.getElementById('modalTotal').textContent = `${data.total_count}개`;
    document.getElementById('modalChange').innerHTML  = Utils.changeText(data.score_change);

    // 미니 바
    if (data.total_count > 0) {
      document.getElementById('barPos').style.width = `${(data.positive_count / data.total_count * 100).toFixed(1)}%`;
      document.getElementById('barNeg').style.width = `${(data.negative_count / data.total_count * 100).toFixed(1)}%`;
      document.getElementById('barNeu').style.width = `${(data.neutral_count  / data.total_count * 100).toFixed(1)}%`;
    }

    // 댓글
    const commentList = document.getElementById('commentList');
    commentList.innerHTML = (data.comments || []).map(c => `
      <div class="comment-item ${c.sentiment}">
        <p style="font-size:0.88rem">${c.content}</p>
        <div class="comment-meta">
          ${c.author} · 👍 ${c.likes} · 출처: ${c.source}
          · ${c.sentiment === 'positive' ? '😊 긍정' : c.sentiment === 'negative' ? '😠 부정' : '😐 중립'}
        </div>
      </div>`).join('');

    // DART 링크
    const dartUrl = `https://dart.fss.or.kr/corp/searchCorp.do?firmName=${encodeURIComponent(data.name)}`;
    document.getElementById('dartLink').href = dartUrl;

    // 점수 추이 차트는 탭 클릭 시 로딩 (성능 최적화)
    if (data.score_history) {
      State.currentStock._history = data.score_history;
    }
  },

  close() {
    this.el.classList.remove('open');
    this.el.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
    if (State.chartInstance) {
      State.chartInstance.destroy();
      State.chartInstance = null;
    }
    State.currentStock = null;
  },
};

// ── 차트 ──────────────────────────────────────────────────────────────────
const ChartModule = {
  async renderScoreChart(code) {
    const canvas = document.getElementById('scoreChart');
    if (!canvas) return;

    // 이전 차트 제거
    if (State.chartInstance) { State.chartInstance.destroy(); }

    let history = State.currentStock?._history;
    if (!history) {
      try { ({ history } = await API.getScoreHistory(code)); }
      catch { return; }
    }

    const labels = history.map(h => h.date.slice(5)); // MM-DD
    const scores = history.map(h => h.score);

    const gradient = canvas.getContext('2d').createLinearGradient(0, 0, 0, 220);
    gradient.addColorStop(0, 'rgba(79,142,247,0.4)');
    gradient.addColorStop(1, 'rgba(79,142,247,0)');

    State.chartInstance = new Chart(canvas, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: '감성점수',
          data: scores,
          borderColor: '#4f8ef7',
          backgroundColor: gradient,
          borderWidth: 2,
          pointRadius: 3,
          pointHoverRadius: 5,
          fill: true,
          tension: 0.4,
        }],
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#1c2230',
            borderColor: '#3a4560',
            borderWidth: 1,
            callbacks: {
              label: ctx => `감성: ${ctx.parsed.y.toFixed(1)}점`,
            },
          },
        },
        scales: {
          x: {
            grid: { color: '#2a3040' },
            ticks: { color: '#8890a8', font: { size: 11 } },
          },
          y: {
            min: 0, max: 100,
            grid: { color: '#2a3040' },
            ticks: { color: '#8890a8', font: { size: 11 }, callback: v => `${v}점` },
          },
        },
      },
    });
  },
};

// ── 카카오 공유 ───────────────────────────────────────────────────────────
const KakaoShare = {
  initialized: false,

  init() {
    if (typeof Kakao !== 'undefined' && KAKAO_JS_KEY && !this.initialized) {
      try {
        Kakao.init(KAKAO_JS_KEY);
        this.initialized = true;
      } catch (e) { console.warn('카카오 SDK 초기화 실패:', e); }
    }
  },

  async shareStock(code) {
    try {
      const data = await API.getShareData(code);

      if (this.initialized && typeof Kakao !== 'undefined') {
        Kakao.Share.sendDefault({
          objectType: 'feed',
          content: {
            title: data.kakao_share.title,
            description: data.kakao_share.description,
            imageUrl: data.kakao_share.image_url,
            link: { mobileWebUrl: data.kakao_share.link_url, webUrl: data.kakao_share.link_url },
          },
          buttons: [{
            title: '상세보기',
            link: { mobileWebUrl: data.kakao_share.link_url, webUrl: data.kakao_share.link_url },
          }],
        });
      } else {
        // 카카오 SDK 없을 때 텍스트 복사 fallback
        await navigator.clipboard.writeText(data.share_text);
        Utils.toast('📋 공유 텍스트가 복사되었습니다!');
      }
    } catch (err) {
      console.error('공유 실패:', err);
      Utils.toast('공유 실패. 링크를 직접 복사해주세요.');
    }
  },
};

// ── 이벤트 바인딩 ─────────────────────────────────────────────────────────
function bindEvents() {
  // 정렬 버튼
  document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      State.sort = btn.dataset.sort;
      State.currentPage = 1;
      loadStocks();
    });
  });

  // 검색
  let searchTimer;
  document.getElementById('searchInput').addEventListener('input', e => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
      State.search = e.target.value.trim();
      State.currentPage = 1;
      loadStocks();
    }, 400);
  });

  // 페이지네이션
  document.getElementById('btnPrev').addEventListener('click', () => {
    if (State.currentPage > 1) { State.currentPage--; loadStocks(); }
  });
  document.getElementById('btnNext').addEventListener('click', () => {
    if (State.currentPage < Math.ceil(State.totalStocks / State.pageSize)) {
      State.currentPage++; loadStocks();
    }
  });
}

// ── 자동 새로고침 (4시간마다) ─────────────────────────────────────────────
function scheduleAutoRefresh() {
  // 1분마다 다음 업데이트 카운트다운 갱신
  setInterval(() => {
    const el = document.getElementById('statNextUpdate');
    if (el) el.textContent = Utils.nextUpdateTime();
  }, 60_000);

  // 4시간마다 데이터 재로딩
  setInterval(() => {
    State.currentPage = 1;
    loadStocks();
  }, 4 * 60 * 60 * 1000);
}

// ── 초기화 ───────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  Modal.init();
  KakaoShare.init();
  bindEvents();
  scheduleAutoRefresh();
  loadStocks();
});
