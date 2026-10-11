// JS puro da tela de comparação. `/compare/data` é uma rota do próprio
// frontend que faz proxy pro backend (usando o JWT da sessão, nunca exposto
// aqui). `run.plots[kind]` vem `null` quando o worker ainda não terminou de
// gerar aquele plot (run processing/failed) — tratado abaixo em vez de
// quebrar a <img>.
(function () {
  const state = { a: null, b: null, plotKind: "measured_predicted" };
  const selectedIds = { a: null, b: null };

  function fmt(value) {
    return typeof value === "number" ? value.toFixed(2) : "—";
  }

  function panelEl(slot) {
    return document.getElementById(`panel-${slot}`);
  }

  function renderEmptyPanel(slot) {
    panelEl(slot).innerHTML = '<p class="text-muted mb-0">Escolha os dois runs e clique em SUBMIT.</p>';
  }

  function renderPanel(slot, run) {
    const hp = Object.entries(run.hyperparams)
      .map(
        ([k, v]) =>
          `<li class="list-group-item d-flex justify-content-between px-0"><span>${k}</span><span>${v}</span></li>`
      )
      .join("");
    const plotUrl = run.plots?.[state.plotKind];
    const plotEl = plotUrl
      ? `<img src="${plotUrl}" alt="${state.plotKind}" class="img-fluid border rounded mb-3" data-plot-img>`
      : `<div class="alert alert-warning mb-3" data-plot-img>Gráfico ainda sendo gerado — recarregue a página em alguns segundos.</div>`;
    panelEl(slot).innerHTML = `
      <h5>${run.name}</h5>
      <span class="badge text-bg-secondary mb-2">${run.algorithm}</span>
      ${plotEl}
      <h6>Hiperparâmetros</h6>
      <ul class="list-group list-group-flush mb-3">${hp || '<li class="list-group-item px-0 text-muted">nenhum</li>'}</ul>
      <h6>Métricas</h6>
      <table class="table table-sm mb-0">
        <thead><tr><th></th><th>RMSE</th><th>MAE</th></tr></thead>
        <tbody>
          <tr><td>treino</td><td>${fmt(run.metrics?.train?.rmse)}</td><td>${fmt(run.metrics?.train?.mae)}</td></tr>
          <tr><td>teste</td><td>${fmt(run.metrics?.test?.rmse)}</td><td>${fmt(run.metrics?.test?.mae)}</td></tr>
        </tbody>
      </table>
    `;
  }

  function renderSlot(slot) {
    if (state[slot]) {
      renderPanel(slot, state[slot]);
    } else {
      renderEmptyPanel(slot);
    }
  }

  // Selecionar só marca qual run cada slot quer — não busca nada ainda.
  // É o SUBMIT que dispara a busca e preenche plot + métricas juntos.
  function onSelectChange(slot, runId) {
    selectedIds[slot] = runId || null;
  }

  function onReset(slot) {
    selectedIds[slot] = null;
    state[slot] = null;
    document.getElementById(`select-${slot}`).value = "";
    renderSlot(slot);
    renderComparisonTable();
  }

  async function submitCompare() {
    const { a, b } = selectedIds;
    if (!a || !b) {
      document.getElementById("comparison-table").innerHTML =
        '<p class="text-muted mb-0">Escolha os dois runs antes de clicar em SUBMIT.</p>';
      return;
    }

    const res = await fetch(`/compare/data?a=${a}&b=${b}`);
    const payload = await res.json();
    state.a = payload.a || null;
    state.b = payload.b || null;
    renderSlot("a");
    renderSlot("b");
    renderComparisonTable();
  }

  function updatePlotImages() {
    ["a", "b"].forEach((slot) => {
      if (state[slot]) renderPanel(slot, state[slot]);
    });
  }

  function renderComparisonTable() {
    const target = document.getElementById("comparison-table");
    if (!state.a || !state.b) {
      target.innerHTML = '<p class="text-muted mb-0">Escolha os dois runs e clique em SUBMIT.</p>';
      return;
    }
    const rows = [
      ["RMSE treino", state.a.metrics?.train?.rmse, state.b.metrics?.train?.rmse],
      ["MAE treino", state.a.metrics?.train?.mae, state.b.metrics?.train?.mae],
      ["RMSE teste", state.a.metrics?.test?.rmse, state.b.metrics?.test?.rmse],
      ["MAE teste", state.a.metrics?.test?.mae, state.b.metrics?.test?.mae],
    ];
    const body = rows
      .map(([label, va, vb]) => {
        const bothNumbers = typeof va === "number" && typeof vb === "number";
        const aWorse = bothNumbers && va > vb;
        const bWorse = bothNumbers && vb > va;
        return `<tr>
          <td>${label}</td>
          <td class="${aWorse ? "text-danger fw-semibold" : ""}">${fmt(va)}</td>
          <td class="${bWorse ? "text-danger fw-semibold" : ""}">${fmt(vb)}</td>
        </tr>`;
      })
      .join("");
    target.innerHTML = `
      <table class="table mb-0">
        <thead><tr><th>Métrica</th><th>${state.a.name}</th><th>${state.b.name}</th></tr></thead>
        <tbody>${body}</tbody>
      </table>
    `;
  }

  document.querySelectorAll("select[data-slot]").forEach((select) => {
    select.addEventListener("change", (e) => {
      onSelectChange(e.target.dataset.slot, e.target.value);
    });
  });

  document.querySelectorAll("[data-reset]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      onReset(e.target.dataset.reset);
    });
  });

  document.querySelectorAll("[data-plot-kind]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      document.querySelectorAll("[data-plot-kind]").forEach((b) => b.classList.remove("active"));
      e.target.classList.add("active");
      state.plotKind = e.target.dataset.plotKind;
      updatePlotImages();
    });
  });

  document.getElementById("submit-compare").addEventListener("click", submitCompare);
})();
