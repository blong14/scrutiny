document.addEventListener("DOMContentLoaded", function (e) {
    const es = new EventSource("//scrutiny.local/.well-known/mercure?topic=news");
    Turbo.connectStreamSource(es);
});
