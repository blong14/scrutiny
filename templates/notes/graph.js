(function (e) {
    const es = new EventSource("/.well-known/mercure?topic=animate-graph");
    Turbo.connectStreamSource(es);
})();
