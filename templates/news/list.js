document.addEventListener("DOMContentLoaded", function (e) {
    const es = new EventSource("//scrutiny.local:8089/.well-known/mercure?topic=news");
    Turbo.connectStreamSource(es);
});
