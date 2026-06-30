/* Service Worker:让网站可安装为 App,并提供基础离线兜底。
   策略:页面/接口走「网络优先」,失败再用缓存;静态资源「缓存优先」。 */
const CACHE = "loan-helper-v1";
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

  const isStatic = url.pathname.startsWith("/static/") || /\.(css|js|png|ico|webmanifest)$/.test(url.pathname);
  if (isStatic) {
    // 缓存优先
    e.respondWith(
      caches.match(req).then((hit) => hit || fetch(req).then((res) => {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(req, copy)).catch(() => {});
        return res;
      }).catch(() => hit))
    );
  } else {
    // 页面:网络优先,失败回退缓存
    e.respondWith(
      fetch(req).then((res) => {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(req, copy)).catch(() => {});
        return res;
      }).catch(() => caches.match(req).then((hit) => hit || caches.match("/")))
    );
  }
});
