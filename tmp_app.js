const $ = (selector) => document.querySelector(selector);
const IMAGE_HISTORY_HYDRATE_LIMIT = 12;
const IMAGE_SUBMIT_TIMEOUT_MS = 120000;

const els = {
  authView: $("#authView"),
  appView: $("#appView"),
  accountBar: $("#accountBar"),
  accountEmail: $("#accountEmail"),
  accountBalance: $("#accountBalance"),
  logoutButton: $("#logoutButton"),
  emailLoginForm: $("#emailLoginForm"),
  loginLinkPanel: $("#loginLinkPanel"),
  loginEmail: $("#loginEmail"),
  loginDevLink: $("#loginDevLink"),
  resendLoginLink: $("#resendLoginLink"),
  plansGrid: $("#plansGrid"),
  ordersList: $("#ordersList"),
  refreshPlans: $("#refreshPlans"),
  refreshOrders: $("#refreshOrders"),
  generateTab: $("#generateTab"),
  editTab: $("#editTab"),
  generateForm: $("#generateForm"),
  editForm: $("#editForm"),
  editSourcePreview: $("#editSourcePreview"),
  generateCost: $("#generateCost"),
  editCost: $("#editCost"),
  authMessage: $("#authMessage"),
  message: $("#message"),
  paymentBox: $("#paymentBox"),
  resultGrid: $("#resultGrid"),
  clearResults: $("#clearResults"),
  adminPanel: $("#adminPanel"),
  planForm: $("#planForm"),
  planSubmit: $("#planSubmit"),
  resetPlanForm: $("#resetPlanForm"),
  adminPlans: $("#adminPlans"),
  adminUserSearchForm: $("#adminUserSearchForm"),
  adminUserSearch: $("#adminUserSearch"),
  adminOrderSearchForm: $("#adminOrderSearchForm"),
  adminOrderSearch: $("#adminOrderSearch"),
  adminOrderStatus: $("#adminOrderStatus"),
  adminUsers: $("#adminUsers"),
  adminOrders: $("#adminOrders"),
  refreshAdmin: $("#refreshAdmin"),
};

let currentUser = null;
let results = [];
let imageJobs = [];
let imageJobPolls = new Map();
let resultKeys = new Set();
let adminPlanCache = [];
let selectedEditSource = null;
let pendingLoginEmail = "";
let paymentPoll = null;

init();

async function init() {
  bindEvents();
  restoreLastEmail();
  const loginToken = consumeLoginTokenFromUrl();
  if (loginToken) {
    await finishEmailLogin(loginToken);
    return;
  }
  await loadMe();
}

function bindEvents() {
  els.emailLoginForm.addEventListener("submit", requestEmailLogin);
  els.resendLoginLink.addEventListener("click", resendLoginLink);
  els.logoutButton.addEventListener("click", logout);
  els.refreshPlans.addEventListener("click", loadPlans);
  els.refreshOrders.addEventListener("click", loadOrders);
  els.generateTab.addEventListener("click", () => setToolMode("generate"));
  els.editTab.addEventListener("click", () => setToolMode("edit"));
  els.generateForm.addEventListener("input", updateCosts);
  els.editForm.addEventListener("input", updateCosts);
  els.generateForm.addEventListener("submit", runGenerate);
  els.editForm.addEventListener("submit", runEdit);
  els.resultGrid.addEventListener("click", selectResultForEdit);
  els.editSourcePreview.addEventListener("click", clearEditSource);
  els.clearResults.addEventListener("click", () => {
    results = [];
    resultKeys.clear();
    imageJobs = imageJobs.filter(isUnfinishedImageJob);
    renderResults();
  });
  els.planForm.addEventListener("submit", savePlan);
  els.resetPlanForm.addEventListener("click", resetPlanForm);
  els.refreshAdmin.addEventListener("click", refreshAdmin);
  els.adminUserSearchForm.addEventListener("submit", searchAdmin);
  els.adminOrderSearchForm.addEventListener("submit", searchAdmin);
  els.adminOrderStatus.addEventListener("change", loadAdmin);
}

async function loadMe() {
  try {
    const data = await api("/api/me");
    await enterApp(data.user);
  } catch {
    showAuth();
  }
}

async function enterApp(user) {
  currentUser = user;
  showApp();
  const initialLoads = [loadPlans(), loadOrders()];
  if (currentUser.role === "admin") {
    initialLoads.push(loadAdmin());
  }
  await Promise.all(initialLoads);
  loadImageHistory(currentUser.id);
}

function showAuth() {
  currentUser = null;
  stopPaymentPolling();
  stopImageJobPolling();
  imageJobs = [];
  results = [];
  resultKeys.clear();
  els.authView.classList.remove("hidden");
  els.appView.classList.add("hidden");
  els.accountBar.classList.add("hidden");
  els.emailLoginForm.classList.remove("hidden");
  els.loginLinkPanel.classList.add("hidden");
}

function showApp() {
  els.authView.classList.add("hidden");
  els.appView.classList.remove("hidden");
  els.accountBar.classList.remove("hidden");
  els.accountEmail.textContent = currentUser.email;
  rememberEmail(currentUser.email);
  renderBalance(currentUser.credits_milli, currentUser.credits_expires_at);
  els.adminPanel.classList.toggle("hidden", currentUser.role !== "admin");
  updateCosts();
}

function renderBalance(value, expiresAt) {
  const suffix = expiresAt ? ` · ${formatExpiry(expiresAt)}` : "";
  els.accountBalance.textContent = `${formatCredits(value)} 图点${suffix}`;
}

function setToolMode(mode) {
  const generate = mode === "generate";
  els.generateTab.classList.toggle("is-active", generate);
  els.editTab.classList.toggle("is-active", !generate);
  els.generateForm.classList.toggle("hidden", !generate);
  els.editForm.classList.toggle("hidden", generate);
}

async function requestEmailLogin(event) {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const email = String(form.get("email") || "").trim();
  if (!email) return setMessage("请填写邮箱", "error");
  rememberEmail(email);
  els.emailLoginForm.querySelector("button[type='submit']").disabled = true;
  try {
    const data = await api("/api/auth/email/start", {
      method: "POST",
      body: JSON.stringify({ email }),
    });
    showLoginLinkPanel(data.email || email, data);
    setMessage("登录邮件已发送", "ok");
  } catch (error) {
    setMessage(error.message, "error");
  } finally {
    els.emailLoginForm.querySelector("button[type='submit']").disabled = false;
  }
}

async function finishEmailLogin(token) {
  try {
    const data = await api("/api/auth/email/consume", {
      method: "POST",
      body: JSON.stringify({ token }),
    });
    await enterApp(data.user);
    setMessage("已登录", "ok");
  } catch {
    await loadMe();
    setMessage("登录链接已失效，请重新发送登录链接。", "error");
  }
}

function showLoginLinkPanel(email, data = {}) {
  pendingLoginEmail = String(email || "").trim();
  setMessage("");
  els.emailLoginForm.classList.add("hidden");
  els.loginLinkPanel.classList.remove("hidden");
  els.loginEmail.textContent = pendingLoginEmail || "你的邮箱";
  renderLoginDevLink(data.login_url);
}

function renderLoginDevLink(url) {
  els.loginDevLink.classList.toggle("hidden", !url);
  els.loginDevLink.innerHTML = url
    ? `开发登录链接：<a href="${escapeHtml(url)}">${escapeHtml(url)}</a>`
    : "";
}

async function resendLoginLink() {
  if (!pendingLoginEmail) {
    els.emailLoginForm.classList.remove("hidden");
    els.loginLinkPanel.classList.add("hidden");
    setMessage("请先填写邮箱。", "error");
    return;
  }
  els.resendLoginLink.disabled = true;
  try {
    const data = await api("/api/auth/email/start", {
      method: "POST",
      body: JSON.stringify({ email: pendingLoginEmail }),
    });
    renderLoginDevLink(data.login_url);
    setMessage("登录邮件已重新发送。", "ok");
  } catch (error) {
    setMessage(error.message, "error");
  } finally {
    els.resendLoginLink.disabled = false;
  }
}

async function logout() {
  stopPaymentPolling();
  stopImageJobPolling();
  await api("/api/auth/logout", { method: "POST" }).catch(() => null);
  showAuth();
}

async function loadPlans() {
  const plans = await api("/api/plans");
  els.plansGrid.innerHTML = plans.map(renderPlan).join("");
  els.plansGrid.querySelectorAll("[data-buy-plan]").forEach((button) => {
    button.addEventListener("click", () => createOrder(button.dataset.buyPlan));
  });
}

function renderPlan(plan) {
  const credits = (plan.credits_milli / 1000).toFixed(0);
  const price = (plan.price_fen / 100).toFixed(2);
  const validity = `${Number(plan.validity_days || 31)} 天有效`;
  return `
    <article class="plan-card">
      <div class="plan-top">
        <span class="plan-name">${escapeHtml(plan.name)}</span>
        <span class="price">¥${price}</span>
      </div>
      <div class="meta">${credits} 标准图点 · ${validity} · ${escapeHtml(plan.description || "")}</div>
      <button type="button" data-buy-plan="${escapeHtml(plan.code)}">创建订单</button>
    </article>
  `;
}

async function createOrder(planCode) {
  try {
    hidePaymentBox();
    stopPaymentPolling();
    const result = await api("/api/orders", {
      method: "POST",
      body: JSON.stringify({ plan_code: planCode }),
    });
    const order = result.order || result;
    const payment = result.payment || null;
    await loadOrders();
    if (currentUser.role === "admin") await loadAdmin();
    if (payment?.h5_url) {
      window.open(payment.h5_url, "_blank", "noopener,noreferrer");
      setMessage(`订单已创建：${order.out_trade_no}，已打开支付页面`, "ok");
      startPaymentPolling(order.out_trade_no);
    } else if (payment?.code_url) {
      renderNativePayment(order, payment);
      setMessage("订单已创建，请使用微信扫码支付", "ok");
      startPaymentPolling(order.out_trade_no);
    } else {
      setMessage(`订单已创建：${order.out_trade_no}`, "ok");
    }
  } catch (error) {
    setMessage(error.message, "error");
  }
}

function renderNativePayment(order, payment) {
  const codeUrl = String(payment.code_url || "");
  const amountFen = Number(order.amount_fen ?? payment.amount ?? 0);
  els.paymentBox.innerHTML = `
    <article class="payment-card">
      <div class="payment-qr"><div id="paymentQrCode" class="qr-code"></div></div>
      <div class="payment-info">
        <h3>微信扫码支付</h3>
        <div class="meta">订单号：${escapeHtml(order.out_trade_no || payment.out_trade_no || "")}</div>
        <div class="payment-amount">¥${(amountFen / 100).toFixed(2)}</div>
        <div id="paymentStatus" class="payment-status">等待支付结果</div>
        <a href="${escapeHtml(codeUrl)}">无法扫码时打开支付链接</a>
      </div>
    </article>
  `;
  renderPaymentQrCode($("#paymentQrCode"), codeUrl);
  els.paymentBox.classList.remove("hidden");
}

function renderPaymentQrCode(container, codeUrl) {
  if (!container) return;
  container.innerHTML = "";
  if (!codeUrl) {
    container.textContent = "未获取到微信支付二维码链接";
    return;
  }
  const QRCodeCtor = window.QRCode;
  if (!QRCodeCtor) {
    container.textContent = codeUrl;
    return;
  }
  try {
    new QRCodeCtor(container, {
      text: codeUrl,
      width: 220,
      height: 220,
      colorDark: "#111827",
      colorLight: "#ffffff",
      correctLevel: QRCodeCtor.CorrectLevel.M,
    });
  } catch (error) {
    console.error("QRCode generation error:", error);
    container.textContent = codeUrl;
  }
}

function hidePaymentBox() {
  els.paymentBox.classList.add("hidden");
  els.paymentBox.innerHTML = "";
}

function startPaymentPolling(outTradeNo) {
  const target = String(outTradeNo || "").trim();
  if (!target) return;
  stopPaymentPolling();
  paymentPoll = {
    outTradeNo: target,
    startedAt: Date.now(),
    attempts: 0,
    timer: null,
  };
  schedulePaymentPoll(1800);
}

function stopPaymentPolling() {
  if (paymentPoll?.timer) window.clearTimeout(paymentPoll.timer);
  paymentPoll = null;
}

function schedulePaymentPoll(delayMs) {
  if (!paymentPoll) return;
  paymentPoll.timer = window.setTimeout(pollPaymentStatus, delayMs);
}

async function pollPaymentStatus() {
  if (!paymentPoll) return;
  const target = paymentPoll.outTradeNo;
  paymentPoll.attempts += 1;
  try {
    const orders = await api("/api/orders");
    renderOrders(orders);
    const order = orders.find((item) => item.out_trade_no === target);
    if (order?.status === "paid") {
      await refreshBalance();
      if (currentUser?.role === "admin") await loadAdmin();
      updatePaymentStatus("支付成功，图点已入账。", "paid");
      setMessage("支付成功，图点已入账。", "ok");
      stopPaymentPolling();
      return;
    }
    if (order && order.status !== "pending") {
      updatePaymentStatus(`订单状态：${statusText(order.status)}`, "error");
      stopPaymentPolling();
      return;
    }
    if (Date.now() - paymentPoll.startedAt > 10 * 60 * 1000) {
      updatePaymentStatus("仍在等待支付结果，可稍后查看订单状态。", "error");
      stopPaymentPolling();
      return;
    }
    updatePaymentStatus("等待支付结果", "");
    schedulePaymentPoll(Math.min(5000, 1800 + paymentPoll.attempts * 300));
  } catch {
    if (!paymentPoll) return;
    schedulePaymentPoll(5000);
  }
}

function updatePaymentStatus(text, kind) {
  const status = $("#paymentStatus");
  if (!status) return;
  status.textContent = text;
  status.classList.toggle("is-paid", kind === "paid");
  status.classList.toggle("is-error", kind === "error");
}

async function loadOrders() {
  const orders = await api("/api/orders");
  renderOrders(orders);
}

function renderOrders(orders) {
  els.ordersList.innerHTML = orders.length
    ? orders.map(renderOrder).join("")
    : `<div class="meta">暂无订单</div>`;
}

function statusText(status) {
  return (
    {
      pending: "待支付",
      paid: "已支付",
      refunding: "退款中",
      refunded: "已退款",
      closed: "已关闭",
    }[status] || status
  );
}

function renderOrder(order) {
  return `
    <article class="list-item">
      <div class="list-top">
        <span class="list-title">${escapeHtml(order.plan_code)}</span>
        <span class="price">${escapeHtml(statusText(order.status))}</span>
      </div>
      <div class="meta">${escapeHtml(order.out_trade_no)} · ¥${(order.amount_fen / 100).toFixed(2)} · ${Number(order.validity_days || 31)} 天</div>
    </article>
  `;
}

async function runGenerate(event) {
  event.preventDefault();
  const form = new FormData(els.generateForm);
  const prompt = String(form.get("prompt") || "").trim();
  const avoid = String(form.get("avoid") || "").trim();
  if (!prompt) return setMessage("请填写提示词", "error");
  if (avoid) form.set("prompt", `${prompt}\n\nAvoid: ${avoid}`);
  form.delete("avoid");
  form.append("operation", "generate");
  await runImageRequest(form, els.generateForm);
}

async function runEdit(event) {
  event.preventDefault();
  const form = new FormData(els.editForm);
  if (!String(form.get("prompt") || "").trim()) return setMessage("请填写修图提示词", "error");
  if (String(form.get("model") || "").trim().toLowerCase() === "gpt-image-2") {
    form.delete("input_fidelity");
  }
  const uploadedImages = removeEmptyFileFields(form, "image");
  removeEmptyFileFields(form, "mask");
  if (selectedEditSource) {
    let sourceFile;
    try {
      sourceFile = await editSourceToFile(selectedEditSource);
    } catch (error) {
      return setMessage(error.message, "error");
    }
    form.delete("image");
    form.append("image", sourceFile, sourceFile.name);
    uploadedImages.forEach((value) => form.append("image", value));
  }
  if (!form.getAll("image").length) return setMessage("请选择原图", "error");
  form.append("operation", "edit");
  await runImageRequest(form, els.editForm);
}

function removeEmptyFileFields(form, name) {
  const values = form.getAll(name);
  form.delete(name);
  const kept = values.filter((value) => !(value instanceof File) || (value.name && value.size > 0));
  kept.forEach((value) => form.append(name, value));
  return kept;
}

async function editSourceToFile(source) {
  const filename = source.filename || "source.png";
  try {
    const response = await fetch(source.src, { credentials: "omit" });
    if (!response.ok) throw new Error("image source fetch failed");
    const blob = await response.blob();
    return new File([blob], filename, { type: imageMimeType(filename, blob.type) });
  } catch {
    throw new Error("这张图片不能直接用于修图，请先下载后上传");
  }
}

function imageMimeType(filename, fallback) {
  if (String(fallback || "").startsWith("image/")) return fallback;
  const ext = String(filename || "").split(".").pop()?.toLowerCase();
  return (
    {
      jpg: "image/jpeg",
      jpeg: "image/jpeg",
      png: "image/png",
      webp: "image/webp",
    }[ext] || "image/png"
  );
}

async function runImageRequest(form, sourceForm) {
  if (sourceForm.dataset.submitting === "true") return;
  sourceForm.dataset.submitting = "true";
  setMessage("任务提交中...", "ok");
  const button = sourceForm.querySelector("button[type='submit']");
  if (button) button.disabled = true;
  try {
    const job = await api("/api/images", {
      method: "POST",
      body: form,
      json: false,
      timeoutMs: IMAGE_SUBMIT_TIMEOUT_MS,
    });
    upsertImageJob(job);
    startImageJobPolling(job.id);
    await refreshBalance();
    setMessage(`任务 #${job.id} 已提交，后台生成中`, "ok");
  } catch (error) {
    await refreshBalance().catch(() => null);
    setMessage(error.message, "error");
  } finally {
    delete sourceForm.dataset.submitting;
    if (button) button.disabled = false;
  }
}

async function refreshBalance() {
  const data = await api("/api/balance");
  currentUser.credits_milli = data.credits_milli;
  currentUser.credits_expires_at = data.credits_expires_at;
  renderBalance(data.credits_milli, data.credits_expires_at);
}

async function loadImageHistory(userId = currentUser?.id) {
  if (!userId || currentUser?.id !== userId) return;
  try {
    const query = currentUser?.role === "admin" ? "?include_response=false" : "";
    const jobs = await api(`/api/images/history${query}`);
    if (!currentUser || currentUser.id !== userId) return;
    imageJobs = Array.isArray(jobs) ? jobs : [];
    results = [];
    resultKeys.clear();
    [...imageJobs].reverse().forEach(importImageJobResults);
    imageJobs.filter(isUnfinishedImageJob).forEach((job) => startImageJobPolling(job.id));
    renderResults();
    hydrateImageHistoryResults(userId);
  } catch (error) {
    console.error("Image history load failed:", error);
    renderResults();
  }
}

async function hydrateImageHistoryResults(userId) {
  if (currentUser?.role !== "admin") return;
  if (!userId || currentUser?.id !== userId) return;
  const jobs = imageJobs
    .filter((job) => job?.status === "succeeded" && !hasImageJobResponseLoaded(job))
    .slice(0, IMAGE_HISTORY_HYDRATE_LIMIT);
  for (const job of jobs) {
    if (!currentUser || currentUser.id !== userId) return;
    try {
      const hydrated = await api(`/api/images/${encodeURIComponent(job.id)}`);
      if (!currentUser || currentUser.id !== userId) return;
      upsertImageJob(hydrated);
    } catch (error) {
      console.error("Image history result hydrate failed:", error);
    }
  }
}

function upsertImageJob(job) {
  if (!job?.id) return;
  const index = imageJobs.findIndex((item) => item.id === job.id);
  if (index >= 0) {
    imageJobs.splice(index, 1, job);
  } else {
    imageJobs.unshift(job);
  }
  importImageJobResults(job);
  renderResults();
}

function importImageJobResults(job) {
  if (job?.status !== "succeeded") return;
  const next = imageResultItemsFromJob(job).filter((item) => !resultKeys.has(item.key));
  next.forEach((item) => resultKeys.add(item.key));
  results = [...next, ...results];
}

function imageResultItemsFromJob(job) {
  const items = Array.isArray(job?.response?.data) ? job.response.data : [];
  if (!items.length) return [];
  const createdAt = fileTimestamp(job.completed_at || job.updated_at || job.created_at);
  const format = normalizeFormat(job.output_format || "png");
  return items
    .map((item, index) => {
      const key = `${job.id}:${index}`;
      const filename = `image-${job.id}-${createdAt}-${index + 1}.${format === "jpeg" ? "jpg" : format}`;
      const base = {
        key,
        jobId: Number(job.id) || 0,
        userId: Number(job.user_id) || 0,
        userEmail: job.user_email || "",
        operation: job.operation || "",
        size: job.size || "",
        quality: job.quality || "",
        createdAt: job.created_at || "",
        sortTime: resultSortTime(job),
        outputIndex: index,
        filename,
      };
      const b64 = String(item?.b64_json || "").trim();
      if (b64) {
        return {
          ...base,
          src: `data:image/${format};base64,${b64}`,
          download: true,
        };
      }
      const url = String(item?.url || "").trim();
      if (url) {
        return {
          ...base,
          src: url,
          download: false,
        };
      }
      return null;
    })
    .filter(Boolean);
}

function resultSortTime(job) {
  const value = Date.parse(job?.created_at || job?.completed_at || job?.updated_at || "");
  return Number.isFinite(value) ? value : 0;
}

function compareResultItems(a, b) {
  const timeDiff = (b.sortTime || 0) - (a.sortTime || 0);
  if (timeDiff) return timeDiff;
  const jobDiff = (b.jobId || 0) - (a.jobId || 0);
  if (jobDiff) return jobDiff;
  return (a.outputIndex || 0) - (b.outputIndex || 0);
}

function startImageJobPolling(jobId) {
  const id = Number(jobId);
  if (!Number.isFinite(id) || id <= 0 || imageJobPolls.has(id)) return;
  scheduleImageJobPoll(id, 1200);
}

function scheduleImageJobPoll(jobId, delayMs) {
  stopImageJobPolling(jobId);
  const timer = window.setTimeout(() => pollImageJob(jobId), delayMs);
  imageJobPolls.set(jobId, timer);
}

function stopImageJobPolling(jobId) {
  if (jobId === undefined) {
    imageJobPolls.forEach((timer) => window.clearTimeout(timer));
    imageJobPolls.clear();
    return;
  }
  const id = Number(jobId);
  const timer = imageJobPolls.get(id);
  if (timer) window.clearTimeout(timer);
  imageJobPolls.delete(id);
}

async function pollImageJob(jobId) {
  stopImageJobPolling(jobId);
  if (!currentUser) return;
  try {
    const job = await api(`/api/images/${encodeURIComponent(jobId)}`);
    upsertImageJob(job);
    if (isUnfinishedImageJob(job)) {
      scheduleImageJobPoll(job.id, job.status === "queued" ? 1800 : 2800);
      return;
    }
    await refreshBalance().catch(() => null);
    if (job.status === "succeeded") {
      setMessage(`任务 #${job.id} 已完成`, "ok");
    } else {
      setMessage(`任务 #${job.id} 失败：${job.error || "预扣图点已退回"}`, "error");
    }
  } catch (error) {
    if (!currentUser) return;
    console.error("Image job poll failed:", error);
    scheduleImageJobPoll(jobId, 5000);
  }
}

function isUnfinishedImageJob(job) {
  return ["reserved", "queued", "processing"].includes(job?.status);
}

function shouldRenderImageJob(job) {
  if (isUnfinishedImageJob(job) || job.status === "failed") return true;
  if (job.status === "succeeded" && !hasImageJobResponseLoaded(job)) return false;
  return !hasImageJobResults(job);
}

function hasImageJobResponseLoaded(job) {
  return job && Object.prototype.hasOwnProperty.call(job, "response") && job.response !== null;
}

function hasImageJobResults(job) {
  return Array.isArray(job?.response?.data)
    && job.response.data.some((item) => item?.b64_json || item?.url);
}

function renderResults() {
  const jobCards = imageJobs.filter(shouldRenderImageJob).map(renderImageJob).join("");
  results.sort(compareResultItems);
  const resultCards = results.map(renderResult).join("");
  els.resultGrid.innerHTML = jobCards || resultCards
    ? `${jobCards}${resultCards}`
    : `<div class="meta">暂无输出</div>`;
}

function renderImageJob(job) {
  const failed = job.status === "failed";
  const working = isUnfinishedImageJob(job);
  const detail = failed
    ? job.error || "生成失败，预扣图点已退回"
    : working
      ? `${imageJobOperationText(job.operation)} · ${Number(job.requested_n || 1)} 张 · ${formatCredits(job.requested_milli)} 图点`
      : "任务完成，但没有可显示的图片结果";
  return `
    <article class="result-item image-job-card ${failed ? "is-error" : ""}">
      <div class="job-preview">
        <span>${escapeHtml(imageJobStatusText(job.status))}</span>
      </div>
      <div class="result-meta">
        <span>任务 #${job.id}</span>
        <strong>${escapeHtml(imageJobStatusText(job.status))}</strong>
      </div>
      <div class="job-detail">${escapeHtml(detail)}</div>
    </article>
  `;
}

function renderResult(item, index) {
  const src = escapeHtml(item.src);
  const filename = escapeHtml(item.filename);
  const openAttrs = item.download ? `download="${filename}"` : 'target="_blank" rel="noreferrer"';
  return `
    <article class="result-item">
      <img src="${src}" alt="输出图片" />
      <div class="result-meta">
        <span>${filename}</span>
        <div class="result-actions">
          <button type="button" data-edit-result="${index}">修图</button>
          <a href="${src}" ${openAttrs}>${item.download ? "下载" : "打开"}</a>
        </div>
      </div>
    </article>
  `;
}

function imageJobStatusText(status) {
  return (
    {
      reserved: "已预扣",
      queued: "排队中",
      processing: "生成中",
      succeeded: "已完成",
      failed: "失败",
    }[status] || status
  );
}

function imageJobOperationText(operation) {
  return operation === "edit" ? "修图" : "作图";
}

function selectResultForEdit(event) {
  const button = event.target.closest?.("[data-edit-result]");
  if (!button) return;
  const index = Number(button.dataset.editResult);
  const source = results[index];
  if (!source) return;
  selectedEditSource = {
    src: source.src,
    filename: source.filename,
  };
  renderEditSourcePreview();
  setToolMode("edit");
  setMessage("已选原图", "ok");
  window.requestAnimationFrame(() => {
    els.editForm.elements.prompt?.focus();
    els.editForm.scrollIntoView({ block: "start", behavior: "smooth" });
  });
}

function renderEditSourcePreview() {
  if (!els.editSourcePreview) return;
  if (!selectedEditSource) {
    els.editSourcePreview.classList.add("hidden");
    els.editSourcePreview.innerHTML = "";
    return;
  }
  els.editSourcePreview.classList.remove("hidden");
  els.editSourcePreview.innerHTML = `
    <img src="${escapeHtml(selectedEditSource.src)}" alt="已选原图" />
    <div class="edit-source-copy">
      <strong>已选原图</strong>
      <span>${escapeHtml(selectedEditSource.filename)}</span>
    </div>
    <button type="button" data-clear-edit-source>移除</button>
  `;
}

function clearEditSource(event) {
  if (!event.target.closest?.("[data-clear-edit-source]")) return;
  selectedEditSource = null;
  renderEditSourcePreview();
  setMessage("已移除原图", "ok");
}

function updateCosts() {
  els.generateCost.textContent = estimateFormCost(els.generateForm).toFixed(3);
  els.editCost.textContent = estimateFormCost(els.editForm).toFixed(3);
}

function estimateFormCost(form) {
  const data = new FormData(form);
  const n = Math.max(1, Math.min(10, Number.parseInt(data.get("n") || "1", 10) || 1));
  const size = String(data.get("size") || "1024x1024");
  const quality = String(data.get("quality") || "medium");
  const [w, h] = size.split("x").map((value) => Number.parseFloat(value));
  const sizeWeight = Number.isFinite(w) && Number.isFinite(h) ? (w * h) / (1024 * 1024) : 1;
  const qualityWeight = quality === "low" ? 0.7 : quality === "high" ? 1.6 : 1;
  return Math.ceil(n * sizeWeight * qualityWeight * 1000) / 1000;
}

async function loadAdmin() {
  if (!currentUser || currentUser.role !== "admin") return;
  const userQuery = buildQuery({ q: els.adminUserSearch.value });
  const orderQuery = buildQuery({
    q: els.adminOrderSearch.value,
    status: els.adminOrderStatus.value,
  });
  const [plans, users, orders] = await Promise.all([
    api("/api/admin/plans"),
    api(`/api/admin/users${userQuery}`),
    api(`/api/admin/orders${orderQuery}`),
  ]);
  adminPlanCache = plans;
  els.adminPlans.innerHTML = plans.length
    ? plans.map(renderAdminPlan).join("")
    : `<div class="meta">暂无套餐</div>`;
  els.adminUsers.innerHTML = users.length
    ? users.map(renderAdminUser).join("")
    : `<div class="meta">暂无用户</div>`;
  els.adminOrders.innerHTML = orders.length
    ? orders.map(renderAdminOrder).join("")
    : `<div class="meta">暂无订单</div>`;
  els.adminPlans.querySelectorAll("[data-edit-plan]").forEach((button) => {
    button.addEventListener("click", () => editPlan(button.dataset.editPlan));
  });
  els.adminUsers.querySelectorAll("[data-add-credits]").forEach((button) => {
    button.addEventListener("click", () =>
      addUserCredits(button.dataset.addCredits, button.dataset.userEmail),
    );
  });
  els.adminUsers.querySelectorAll("[data-delete-user]").forEach((button) => {
    button.addEventListener("click", () =>
      deleteUser(button.dataset.deleteUser, button.dataset.userEmail),
    );
  });
  els.adminOrders.querySelectorAll("[data-mark-paid]").forEach((button) => {
    button.addEventListener("click", () => markPaid(button.dataset.markPaid));
  });
  els.adminOrders.querySelectorAll("[data-refund-order]").forEach((button) => {
    button.addEventListener("click", () => refundOrder(button.dataset.refundOrder));
  });
  els.adminOrders.querySelectorAll("[data-restore-refund]").forEach((button) => {
    button.addEventListener("click", () => restoreRefundingOrder(button.dataset.restoreRefund));
  });
}

function refreshAdmin() {
  loadAdmin();
}

function searchAdmin(event) {
  event.preventDefault();
  loadAdmin();
}

function renderAdminPlan(plan) {
  const status = plan.active ? "上架" : "下架";
  const validity = `${Number(plan.validity_days || 31)} 天`;
  return `
    <article class="list-item">
      <div class="list-top">
        <span class="list-title">${escapeHtml(plan.name)}</span>
        <span class="price">¥${formatMoney(plan.price_fen)}</span>
      </div>
      <div class="meta">${escapeHtml(plan.code)} · ${formatCredits(plan.credits_milli)} 图点 · ${validity} · ${status} · 排序 ${plan.sort_order}</div>
      <div class="meta">${escapeHtml(plan.description || "")}</div>
      <div class="item-actions">
        <button type="button" data-edit-plan="${escapeHtml(plan.code)}">编辑</button>
      </div>
    </article>
  `;
}

function editPlan(code) {
  const plan = adminPlanCache.find((item) => item.code === code);
  if (!plan) return;
  const form = els.planForm;
  form.elements.code.value = plan.code;
  form.elements.code.readOnly = true;
  form.elements.name.value = plan.name;
  form.elements.price_yuan.value = formatMoney(plan.price_fen);
  form.elements.credits.value = formatDecimalInput(plan.credits_milli / 1000, 3);
  form.elements.validity_days.value = plan.validity_days || 31;
  form.elements.sort_order.value = plan.sort_order;
  form.elements.description.value = plan.description || "";
  form.elements.active.checked = Boolean(plan.active);
  els.planSubmit.textContent = "保存修改";
  form.scrollIntoView({ block: "start", behavior: "smooth" });
}

function resetPlanForm() {
  els.planForm.reset();
  els.planForm.elements.code.readOnly = false;
  els.planForm.elements.validity_days.value = "31";
  els.planForm.elements.sort_order.value = "100";
  els.planForm.elements.active.checked = true;
  els.planSubmit.textContent = "保存套餐";
}

function renderAdminUser(user) {
  const status = user.status ? "启用" : "停用";
  const role = user.role === "admin" ? "管理员" : "用户";
  const lastPaid = user.last_paid_at ? formatDateTime(user.last_paid_at) : "无充值";
  const expiresAt = user.credits_expires_at ? formatExpiry(user.credits_expires_at) : "无到期";
  const action =
    user.role === "admin"
      ? ""
      : `<div class="item-actions">
          <button type="button" data-add-credits="${user.id}" data-user-email="${escapeHtml(user.email)}">加额度</button>
          <button type="button" data-delete-user="${user.id}" data-user-email="${escapeHtml(user.email)}">删除账号</button>
        </div>`;
  return `
    <article class="list-item">
      <div class="list-top">
        <span class="list-title">${escapeHtml(user.email)}</span>
        <span class="price">${formatCredits(user.credits_milli)} 图点</span>
      </div>
      <div class="meta">#${user.id} · ${role} · ${status} · 注册 ${formatDateTime(user.created_at)}</div>
      <div class="meta">${expiresAt} · 累计充值 ¥${formatMoney(user.paid_amount_fen)} · ${formatCredits(user.paid_credits_milli)} 图点 · ${user.paid_orders} 单 · 最近 ${lastPaid}</div>
      ${action}
    </article>
  `;
}

function renderAdminOrder(order) {
  const userEmail = order.user_email ? ` · ${escapeHtml(order.user_email)}` : "";
  const markPaidAction =
    order.status === "pending"
      ? `<button type="button" data-mark-paid="${escapeHtml(order.out_trade_no)}">标记已支付</button>`
      : "";
  const refundAction =
    order.status === "paid"
      ? `<button type="button" data-refund-order="${escapeHtml(order.out_trade_no)}">原路退款</button>`
      : "";
  const restoreRefundAction =
    order.status === "refunding"
      ? `<button type="button" data-restore-refund="${escapeHtml(order.out_trade_no)}">恢复订单</button>`
      : "";
  const actions =
    markPaidAction || refundAction || restoreRefundAction
      ? `<div class="item-actions">${markPaidAction}${refundAction}${restoreRefundAction}</div>`
      : "";
  return `
    <article class="list-item">
      <div class="list-top">
        <span class="list-title">${escapeHtml(order.out_trade_no)}${userEmail}</span>
        <span class="price">${escapeHtml(statusText(order.status))}</span>
      </div>
      <div class="meta">user #${order.user_id} · ${escapeHtml(order.plan_code)} · ${formatCredits(order.credits_milli)} 图点 · ${Number(order.validity_days || 31)} 天</div>
      ${actions}
    </article>
  `;
}

async function markPaid(outTradeNo) {
  await api(`/api/admin/orders/${encodeURIComponent(outTradeNo)}/mark-paid`, { method: "POST" });
  await Promise.all([loadOrders(), loadAdmin(), refreshBalance()]);
  setMessage("已标记支付并入账", "ok");
}

async function addUserCredits(userId, email) {
  const amount = window.prompt(`给 ${email || `user #${userId}`} 增加多少图点？`, "10");
  if (amount === null) return;
  const credits = Number(amount);
  if (!Number.isFinite(credits) || credits <= 0) return setMessage("加额度数量无效", "error");
  await api(`/api/admin/users/${encodeURIComponent(userId)}/credits`, {
    method: "POST",
    body: JSON.stringify({
      amount_milli: Math.round(credits * 1000),
      validity_days: 31,
      reference: "admin-ui",
    }),
  });
  await Promise.all([loadAdmin(), currentUser?.id === Number(userId) ? refreshBalance() : null]);
  setMessage("额度已增加，31 天有效", "ok");
}

async function deleteUser(userId, email) {
  if (currentUser?.id === Number(userId)) return setMessage("不能删除当前管理员账号", "error");
  const confirmed = window.confirm(
    `确认删除 ${email || `user #${userId}`}？此操作不会自动退款，会删除该用户的登录态、订单和生成记录。`,
  );
  if (!confirmed) return;
  await api(`/api/admin/users/${encodeURIComponent(userId)}`, { method: "DELETE" });
  await loadAdmin();
  setMessage("账号已删除", "ok");
}

async function refundOrder(outTradeNo) {
  const confirmed = window.confirm(
    `确认对订单 ${outTradeNo} 发起原路退款？本地会按当前可扣图点比例折算退款金额并先扣回图点，ypay 另扣 10% 手续费。`,
  );
  if (!confirmed) return;
  const reason = window.prompt("退款原因", "admin refund");
  if (reason === null) return;
  const result = await api(`/api/admin/orders/${encodeURIComponent(outTradeNo)}/refund`, {
    method: "POST",
    body: JSON.stringify({ reason }),
  });
  await Promise.all([loadOrders(), loadAdmin(), refreshBalance()]);
  const message = result?.attention_required
    ? "ypay 退款请求结果不确定，已保持退款中并通知管理员核查"
    : result?.order?.status === "refunding"
      ? "已发起原路退款并扣回图点，等待退款确认"
      : "已确认退款并扣回图点";
  setMessage(
    message,
    "ok",
  );
}

async function restoreRefundingOrder(outTradeNo) {
  const confirmed = window.confirm(
    `仅在确认 ypay/微信后台没有创建退款，或退款已失败/关闭但回调未到达时恢复订单 ${outTradeNo}。确认恢复？`,
  );
  if (!confirmed) return;
  const reason = window.prompt("恢复原因", "ypay refund not created");
  if (reason === null) return;
  await api(`/api/admin/orders/${encodeURIComponent(outTradeNo)}/refund/restore`, {
    method: "POST",
    body: JSON.stringify({ reason }),
  });
  await Promise.all([loadOrders(), loadAdmin(), refreshBalance()]);
  setMessage("订单已恢复为已支付，并返还预扣图点", "ok");
}

async function savePlan(event) {
  event.preventDefault();
  const form = new FormData(els.planForm);
  const priceYuan = Number(form.get("price_yuan"));
  const credits = Number(form.get("credits"));
  const validityDays = Number.parseInt(form.get("validity_days") || "31", 10);
  if (!Number.isFinite(priceYuan) || priceYuan < 0) return setMessage("套餐价格无效", "error");
  if (!Number.isFinite(credits) || credits <= 0) return setMessage("套餐额度无效", "error");
  if (!Number.isInteger(validityDays) || validityDays <= 0) return setMessage("套餐有效期无效", "error");
  try {
    await api("/api/admin/plans", {
      method: "POST",
      body: JSON.stringify({
        code: form.get("code"),
        name: form.get("name"),
        price_fen: Math.round(priceYuan * 100),
        credits_milli: Math.round(credits * 1000),
        validity_days: validityDays,
        description: form.get("description"),
        active: form.get("active") === "on",
        sort_order: Number(form.get("sort_order") || 100),
      }),
    });
    resetPlanForm();
    await Promise.all([loadPlans(), loadAdmin()]);
    setMessage("套餐已保存", "ok");
  } catch (error) {
    setMessage(error.message, "error");
  }
}

async function api(url, options = {}) {
  const { timeoutMs, json, ...requestOptions } = options;
  const init = {
    credentials: "same-origin",
    headers: {},
    ...requestOptions,
  };
  let timeout = null;
  let controller = null;
  if (timeoutMs) {
    controller = new AbortController();
    init.signal = controller.signal;
    timeout = window.setTimeout(() => controller.abort(), timeoutMs);
  }
  if (requestOptions.body && json !== false && !(requestOptions.body instanceof FormData)) {
    init.headers["content-type"] = "application/json";
  }
  try {
    const response = await fetch(url, init);
    const text = await response.text();
    const data = parseJson(text);
    if (!response.ok) {
      const error = new Error(data?.error?.message || data?.message || text || `HTTP ${response.status}`);
      error.data = data;
      throw error;
    }
    return data;
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error("提交请求超时，请稍后重试。");
    }
    throw error;
  } finally {
    if (timeout) window.clearTimeout(timeout);
  }
}

function parseJson(text) {
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return { message: text };
  }
}

function setMessage(text, type) {
  const target = els.authView.classList.contains("hidden") ? els.message : els.authMessage;
  [els.authMessage, els.message].forEach((node) => {
    node.classList.add("hidden");
    node.classList.remove("ok");
    node.textContent = "";
  });
  if (!text) return;
  target.classList.remove("hidden");
  target.classList.toggle("ok", type === "ok");
  target.textContent = text;
}

function restoreLastEmail() {
  const saved = window.localStorage.getItem("xabcimg_email") || "";
  const input = els.emailLoginForm?.elements?.email;
  if (input && saved && !input.value) input.value = saved;
}

function rememberEmail(email) {
  const value = String(email || "").trim();
  if (value) window.localStorage.setItem("xabcimg_email", value);
}

function formatMoney(amountFen) {
  return (Number(amountFen || 0) / 100).toFixed(2);
}

function formatCredits(creditsMilli) {
  return (Number(creditsMilli || 0) / 1000).toFixed(3);
}

function formatExpiry(value) {
  return `有效至 ${formatDateTime(value)}`;
}

function formatDecimalInput(value, digits) {
  return Number(value || 0)
    .toFixed(digits)
    .replace(/\.?0+$/, "");
}

function formatDateTime(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "-";
  return date.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function fileTimestamp(value) {
  const date = new Date(value);
  const safeDate = Number.isNaN(date.getTime()) ? new Date() : date;
  return safeDate.toISOString().replace(/[:.]/g, "-");
}

function consumeLoginTokenFromUrl() {
  const params = new URLSearchParams(window.location.search);
  const token = params.get("login_token");
  if (!token) return "";
  params.delete("login_token");
  const query = params.toString();
  const next = `${window.location.pathname}${query ? `?${query}` : ""}${window.location.hash}`;
  window.history.replaceState({}, "", next);
  return token;
}

function normalizeFormat(value) {
  return value === "jpg" ? "jpeg" : value || "png";
}

function buildQuery(values) {
  const params = new URLSearchParams();
  Object.entries(values).forEach(([key, value]) => {
    const text = String(value || "").trim();
    if (text) params.set(key, text);
  });
  const query = params.toString();
  return query ? `?${query}` : "";
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}
