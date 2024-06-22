document.addEventListener("DOMContentLoaded", function (e) {
    const es = new EventSource("{{ topic }}");
    Turbo.connectStreamSource(es);
});
