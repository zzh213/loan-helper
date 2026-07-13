/* Service Worker:让网站可安装为 App,并提供基础离线兜底。
   策略:HTML/JS/CSS 走「网络优先」(确保代码更新即时生效),失败再用缓存;
        图片/字体等不常变的资源走「缓存优先」。 */
const CACHE = "loan-helper-v2";
const CORE = ["/", "/static/style.css", "/static/app.js", "/static/avatars.js", "/static/manifest.webmanifest", "/static/icon-192.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(CORE).catch(() => {})));
  self.skipWaiting();
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
  );
  self.clients.claim();
});

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  // 接口与流式:不缓存,直连网络
  if (url.pathname.startsWith("/api/")) return;

  // 代码与页面(HTML/JS/CSS):网络优先,拿到最新版即时生效,离线才回退缓存
  const isCode = /\.(css|js)$/.test(url.pathname);
  const isPage = url.pathname === "/" || (!/\.[a-z0-9]+$/i.test(url.pathname));
  if (isCode || isPage) {
    e.respondWith(
      fetch(req).then((res) => {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(req, copy)).catch(() => {});
        return res;
      }).catch(() => caches.match(req).then((hit) => hit || caches.match("/")))
    );
    return;
  }

  // 其余静态资源(图片/图标/字体等):缓存优先
  const isStatic = url.pathname.startsWith("/static/") || /\.(png|ico|jpg|jpeg|svg|webmanifest|woff2?)$/.test(url.pathname);
  if (isStatic) {
    e.respondWith(
      caches.match(req).then((hit) => hit || fetch(req).then((res) => {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(req, copy)).catch(() => {});
        return res;
      }).catch(() => hit))
    );
  }
});
