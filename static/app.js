// ── HTB RAG Web Client Logic ───────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  // Elements
  const queryInput = document.getElementById('queryInput');
  const submitBtn = document.getElementById('submitBtn');
  const clearBtn = document.getElementById('clearBtn');
  const chips = document.querySelectorAll('.chip');
  const osSegmentBtns = document.querySelectorAll('#osFilterGroup .segment-btn');
  const diffFilter = document.getElementById('diffFilter');
  const topKSlider = document.getElementById('topKSlider');
  const topKValue = document.getElementById('topKValue');

  const statusBadge = document.getElementById('statusBadge');
  const statusText = document.getElementById('statusText');
  const footerStats = document.getElementById('footerStats');

  const resultsSection = document.getElementById('resultsSection');
  const emptyState = document.getElementById('emptyState');
  const loadingIndicator = document.getElementById('loadingIndicator');
  const loadingStep = document.getElementById('loadingStep');

  const responseQueryTitle = document.getElementById('responseQueryTitle');
  const timingBadge = document.getElementById('timingBadge');
  const copyAnswerBtn = document.getElementById('copyAnswerBtn');
  const sourcesList = document.getElementById('sourcesList');
  const answerBody = document.getElementById('answerBody');

  const graphCats = document.getElementById('graphCats');
  const graphTechs = document.getElementById('graphTechs');
  const graphToolsCves = document.getElementById('graphToolsCves');
  const chunksAccordion = document.getElementById('chunksAccordion');

  let activeOS = '';
  let lastRawAnswer = '';

  // ── Initialize Status Check ───────────────────────────────────────────────
  async function checkHealth() {
    try {
      const resp = await fetch('/health');
      if (resp.ok) {
        const data = await resp.json();
        statusBadge.classList.remove('pulse');
        statusText.textContent = `Online: ${data.chunks_indexed.toLocaleString()} chunks`;
        footerStats.textContent = `Indexed: ${data.chunks_indexed.toLocaleString()} Chunks | ${data.graph_nodes.toLocaleString()} Nodes | ${data.graph_edges.toLocaleString()} Edges`;
      } else {
        statusText.textContent = 'API Error';
      }
    } catch (err) {
      statusText.textContent = 'Offline';
    }
  }

  checkHealth();

  // ── Top-K Slider Binding ──────────────────────────────────────────────────
  topKSlider.addEventListener('input', (e) => {
    topKValue.textContent = e.target.value;
  });

  // ── OS Segmented Control ──────────────────────────────────────────────────
  osSegmentBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      osSegmentBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      activeOS = btn.getAttribute('data-os') || '';
    });
  });

  // ── Input & Clear Controls ────────────────────────────────────────────────
  queryInput.addEventListener('input', () => {
    clearBtn.style.display = queryInput.value.trim() ? 'block' : 'none';
  });

  clearBtn.addEventListener('click', () => {
    queryInput.value = '';
    clearBtn.style.display = 'none';
    queryInput.focus();
  });

  // ── Quick Chips ───────────────────────────────────────────────────────────
  chips.forEach(chip => {
    chip.addEventListener('click', () => {
      const q = chip.getAttribute('data-query');
      if (q) {
        queryInput.value = q;
        clearBtn.style.display = 'block';
        performSearch(q);
      }
    });
  });

  // ── Enter Key Trigger ─────────────────────────────────────────────────────
  queryInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      const q = queryInput.value.trim();
      if (q) performSearch(q);
    }
  });

  submitBtn.addEventListener('click', () => {
    const q = queryInput.value.trim();
    if (q) performSearch(q);
  });

  // ── Copy Answer ───────────────────────────────────────────────────────────
  copyAnswerBtn.addEventListener('click', async () => {
    if (!lastRawAnswer) return;
    try {
      await navigator.clipboard.writeText(lastRawAnswer);
      const span = copyAnswerBtn.querySelector('span');
      const originalText = span.textContent;
      span.textContent = 'Copied!';
      setTimeout(() => { span.textContent = originalText; }, 2000);
    } catch (err) {
      console.error('Failed to copy', err);
    }
  });

  // ── Search Execution ──────────────────────────────────────────────────────
  async function performSearch(query) {
    // UI state: loading
    emptyState.style.display = 'none';
    resultsSection.style.display = 'none';
    loadingIndicator.style.display = 'flex';
    submitBtn.disabled = true;
    loadingStep.textContent = 'Querying BM25, Gemini vectors & NetworkX graph...';

    const startTime = performance.now();

    try {
      // Step 1: Request synthesis from /query
      const payload = {
        question: query,
        top_k: parseInt(topKSlider.value, 10),
        os: activeOS || null,
        difficulty: diffFilter.value || null,
      };

      // Also fetch raw retrieval for the chunks accordion in parallel
      const [queryResp, retrieveResp] = await Promise.all([
        fetch('/query', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        }),
        fetch('/retrieve', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question: query, top_k: parseInt(topKSlider.value, 10) }),
        })
      ]);

      if (!queryResp.ok) {
        throw new Error(`Server returned error ${queryResp.status}`);
      }

      const queryData = await queryResp.json();
      const retrieveData = retrieveResp.ok ? await retrieveResp.json() : null;

      const duration = ((performance.now() - startTime) / 1000).toFixed(2);
      timingBadge.textContent = `⏱️ ${duration}s`;

      renderResults(query, queryData, retrieveData);

    } catch (err) {
      console.error(err);
      loadingIndicator.style.display = 'none';
      resultsSection.style.display = 'block';
      answerBody.innerHTML = `<div style="color: #ef4444; padding: 1rem; background: rgba(239,68,68,0.1); border-radius: 8px;">
        <strong>Error:</strong> Failed to fetch answer (${err.message}). Make sure the API server is running with valid API keys.
      </div>`;
    } finally {
      loadingIndicator.style.display = 'none';
      submitBtn.disabled = false;
    }
  }

  // ── Render Response & Evidence ────────────────────────────────────────────
  function renderResults(query, queryData, retrieveData) {
    resultsSection.style.display = 'flex';
    responseQueryTitle.textContent = query;
    lastRawAnswer = queryData.answer || '';

    // 1. Render Answer Markdown
    if (typeof marked !== 'undefined') {
      answerBody.innerHTML = marked.parse(queryData.answer);
    } else {
      answerBody.textContent = queryData.answer;
    }

    // 2. Render Citations Badges
    sourcesList.innerHTML = '';
    const sources = queryData.sources || [];
    if (sources.length > 0) {
      sources.forEach(src => {
        const span = document.createElement('span');
        span.className = 'source-badge';
        span.textContent = src;
        sourcesList.appendChild(span);
      });
    } else {
      sourcesList.innerHTML = '<span style="color: var(--text-dim); font-size: 0.8rem;">No explicit machines cited</span>';
    }

    // 3. Render Knowledge Graph Findings
    graphCats.innerHTML = '';
    graphTechs.innerHTML = '';
    graphToolsCves.innerHTML = '';

    const graph = retrieveData?.graph || {};
    const cats = graph.matched_categories || [];
    const techs = graph.matched_techniques || [];
    const tools = graph.matched_tools || [];
    const cves = graph.matched_cves || [];

    if (cats.length > 0) {
      cats.forEach(c => appendTag(graphCats, c, 'tag-cat'));
    } else {
      graphCats.innerHTML = '<span style="color: var(--text-dim); font-size: 0.75rem;">None</span>';
    }

    if (techs.length > 0) {
      techs.slice(0, 15).forEach(t => appendTag(graphTechs, t, 'tag-tech'));
    } else {
      graphTechs.innerHTML = '<span style="color: var(--text-dim); font-size: 0.75rem;">None</span>';
    }

    const combinedToolsCves = [...tools, ...cves];
    if (combinedToolsCves.length > 0) {
      combinedToolsCves.forEach(tc => appendTag(graphToolsCves, tc, 'tag-tool'));
    } else {
      graphToolsCves.innerHTML = '<span style="color: var(--text-dim); font-size: 0.75rem;">None</span>';
    }

    // 4. Render Retrieved Chunks Accordion
    chunksAccordion.innerHTML = '';
    const chunks = retrieveData?.chunks || [];
    if (chunks.length > 0) {
      chunks.forEach((chunk, idx) => {
        const meta = chunk.metadata || {};
        const item = document.createElement('div');
        item.className = 'chunk-item';

        const header = document.createElement('div');
        header.className = 'chunk-header';
        header.innerHTML = `
          <div class="chunk-source-group">
            <span class="chunk-rank">#${idx + 1}</span>
            <span class="chunk-source">${escapeHtml(meta.source || 'unknown')}</span>
            <span class="chunk-phase">${escapeHtml(meta.attack_phase || 'general')}</span>
          </div>
          <span style="font-size: 0.75rem; color: var(--text-dim); font-family: var(--font-mono);">
            Score: ${(chunk.rrf_score || chunk.score || 0).toFixed(4)} ▾
          </span>
        `;

        const body = document.createElement('div');
        body.className = 'chunk-body';
        body.textContent = chunk.text || '';

        header.addEventListener('click', () => {
          item.classList.toggle('open');
        });

        item.appendChild(header);
        item.appendChild(body);
        chunksAccordion.appendChild(item);
      });
    } else {
      chunksAccordion.innerHTML = '<div style="color: var(--text-dim); font-size: 0.85rem; padding: 1rem;">No retrieved chunk excerpts available.</div>';
    }

    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function appendTag(container, text, className) {
    const span = document.createElement('span');
    span.className = `tag-item ${className}`;
    span.textContent = text;
    container.appendChild(span);
  }

  function escapeHtml(str) {
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
});
