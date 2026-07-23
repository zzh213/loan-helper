/* Service Worker:让网站可安装为 App,并提供基础离线兜底。
   策略:HTML/JS/CSS 走「网络优先 + 超时兜底」——正常情况下拿最新代码即时生效;
        当服务器休眠冷启动、网络迟迟不响应(超过 SHELL_TIMEOUT)时,先用缓存把页面
        秒显示出来,避免白屏干等十几秒,同时后台继续更新缓存;
        图片/字体等不常变的资源走「缓存优先」。 */
const CACHE = "loan-helper-v3";
const SHELL_TIMEOUT = 3000;  // 网络多久没响应就先用缓存兜底(毫秒)
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

  // 代码与页面(HTML/JS/CSS):网络优先 + 超时兜底
  //  正常:网络通常 1 秒内返回,拿到最新版即时生效并刷新缓存;
  //  冷启动:服务器休眠恢复慢,超过 SHELL_TIMEOUT 仍未响应,则先用缓存秒显示页面,
  //         网络真正返回后再静默更新缓存,下次访问即是最新。
  const isCode = /\.(css|js)$/.test(url.pathname);
  const isPage = url.pathname === "/" || (!/\.[a-z0-9]+$/i.test(url.pathname));
  if (isCode || isPage) {
    e.respondWith(
      caches.match(req).then((cached) => {
        const network = fetch(req).then((res) => {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(req, copy)).catch(() => {});
          return res;
        });
        // 无缓存:只能等网络(离线则回退首页)
        if (!cached) {
          return network.catch(() => caches.match("/"));
        }
        // 有缓存:网络与「超时→用缓存」赛跑,谁先谁赢;网络失败也回退缓存
        const timeout = new Promise((resolve) => setTimeout(() => resolve(cached), SHELL_TIMEOUT));
        return Promise.race([network.catch(() => cached), timeout]);
      })
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
