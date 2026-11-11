// Il token appartiene alla sessione di questa installazione.
(() => {
  const originalFetch = window.fetch.bind(window);
  window.fetch = (input, options = {}) => {
    const url = new URL(input instanceof Request ? input.url : input, location.href);
    const method = (options.method || (input instanceof Request ? input.method : "GET")).toUpperCase();
    if (url.origin === location.origin && !["GET", "HEAD", "OPTIONS"].includes(method)) {
      const headers = new Headers(options.headers || (input instanceof Request ? input.headers : {}));
      const token = document.querySelector('meta[name="csrf-token"]')?.content;
      if (token) headers.set("X-CSRFToken", token);
      options = { ...options, headers };
    }
    return originalFetch(input, options);
  };
})();
