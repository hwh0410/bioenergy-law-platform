<script setup>
import { ref, onMounted, onUnmounted } from "vue";
import { onAuthStateChanged, signInWithPopup, signOut } from "firebase/auth";
import { auth, configured, provider } from "./firebase";

const apiBase = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");
const account = ref(null);
const team = ref(null);
const status = ref("");
const busy = ref(false);
let unsubscribe = () => {};

async function checkPermission() {
  team.value = null;
  if (!auth?.currentUser) return;
  if (!apiBase) {
    status.value = "Google 登入成功；尚未部署權限驗證後端，內部功能暫不開放。";
    return;
  }
  status.value = "正在檢查內部成員權限…";
  try {
    const token = await auth.currentUser.getIdToken();
    const response = await fetch(apiBase + "/api/me", { headers: { Authorization: "Bearer " + token } });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.detail || "HTTP " + response.status);
    team.value = data;
    status.value = "授權成功！";
  } catch (error) {
    status.value = "尚未通過內部授權：" + error.message;
  }
}
async function login() {
  busy.value = true;
  try { await signInWithPopup(auth, provider); }
  catch (error) { status.value = "Google 登入失敗：" + (error.code || error.message); }
  finally { busy.value = false; }
}
async function logout() {
  await signOut(auth);
  team.value = null;
  status.value = "已登出。";
}
onMounted(() => {
  if (!auth) return;
  unsubscribe = onAuthStateChanged(auth, async (user) => {
    account.value = user;
    if (user) await checkPermission();
    else team.value = null;
  });
});
onUnmounted(() => unsubscribe());
</script>

<template>
  <div class="shell">
    <header class="top">
      <div class="brand"><span class="mark">♻</span><div><strong>生質能源法規導航</strong><small>Bioenergy Regulatory Navigator</small></div></div>
      <span class="version">內部團隊測試版 · v0.1</span>
    </header>
    <main>
      <div class="eyebrow">TAIWAN · BIOENERGY COMPLIANCE</div>
      <h1>生質能法規與<br>建廠行政決策平台</h1>
      <p class="lead">整合經濟部、環境部與農業部相關規範，逐步建立建廠行政申辦與補助導航。</p>
      <section class="panel">
        <div class="title"><h2>內部成員入口</h2><span class="pill" :class="{ green: !!team }">{{ team ? "已授權" : "尚未授權" }}</span></div>
        <div v-if="!configured" class="alert">尚未填入 Firebase 設定。請先至 GitHub Repository 設定 VITE_FIREBASE_* 四個變數，再重新執行網頁部署。</div>
        <div v-else-if="!account">
          <p>請先透過 Google 帳號登入。是否能使用內部資料，仍由私有 Google Sheets 名單確認。</p>
          <button class="primary" :disabled="busy" @click="login">{{ busy ? "登入中…" : "使用 Google 帳號登入" }}</button>
        </div>
        <div v-else>
          <div class="field"><span>已登入 Google 帳號</span><strong>{{ account.email }}</strong></div>
          <div class="field"><span>Firebase UID（供管理員加入白名單）</span><code>{{ account.uid }}</code></div>
          <div v-if="team" class="allowed">已核准：{{ team.name || team.email }}，角色 {{ team.role }}</div>
          <div v-else class="alert">Google 登入不等於內部權限。後端授權完成前不會開放內部資料。</div>
          <div class="actions"><button @click="checkPermission">重新檢查權限</button><button @click="logout">登出</button></div>
        </div>
        <p v-if="status" role="status" class="status">{{ status }}</p>
      </section>
      <section class="modules">
        <h2>預計建置的功能</h2>
        <div class="grid">
          <article><small>01</small><h3>法規資料庫</h3><p>中央法規、主管機關與條文版本管理</p></article>
          <article><small>02</small><h3>建廠申辦導航</h3><p>條件評估、行政許可與應備文件</p></article>
          <article><small>03</small><h3>補助媒合</h3><p>補助條件、期限與資格檢核</p></article>
        </div>
      </section>
    </main>
    <footer>目前為登入功能雛形。勿將內部資料或業主機密放入公開 GitHub Pages 檔案。</footer>
  </div>
</template>
