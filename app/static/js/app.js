/**
 * app.js — Scripts globais do sistema Financeiro
 * Funções aqui se aplicam a TODAS as páginas.
 * Scripts específicos de cada página ficam no bloco {% block scripts_extras %}.
 */

// ================================================================
// CURSOR CUSTOMIZADO
// Desativado em dispositivos touch (pointer: coarse)
// ================================================================
(function initCursor() {
    if (window.matchMedia("(pointer: coarse)").matches) return;

    const dot   = document.getElementById("cursor-dot");
    const ring  = document.getElementById("cursor-ring");
    const inner = document.getElementById("cursor-ring-inner");
    if (!dot || !ring || !inner) return;

    // Posição atual do cursor (instantânea)
    let mouseX = -100, mouseY = -100;
    // Posição do trail (com lerp)
    let trailX = -100, trailY = -100;
    document.addEventListener("mousemove", (e) => {
        mouseX = e.clientX;
        mouseY = e.clientY;
        // Dot segue instantaneamente
        dot.style.left = mouseX + "px";
        dot.style.top  = mouseY + "px";
    });

    // Trail com lerp (suavidade)
    function animateTrail() {
        trailX += (mouseX - trailX) * 0.12;
        trailY += (mouseY - trailY) * 0.12;

        ring.style.left  = trailX + "px";
        ring.style.top   = trailY + "px";

        inner.style.left = trailX + "px";
        inner.style.top  = trailY + "px";

        requestAnimationFrame(animateTrail);
    }
    animateTrail();

    // Hover em elementos interativos — aumenta o cursor
    const interativos = "a, button, input, select, textarea, label[for], [role='button']";

    document.addEventListener("mouseover", (e) => {
        if (e.target.closest(interativos)) {
            document.body.classList.add("cursor-hover");
        }
    });

    document.addEventListener("mouseout", (e) => {
        if (e.target.closest(interativos)) {
            document.body.classList.remove("cursor-hover");
        }
    });

    // Esconde cursor ao sair da janela
    document.addEventListener("mouseleave", () => {
        dot.style.opacity  = "0";
        ring.style.opacity = "0";
        inner.style.opacity = "0";
    });

    document.addEventListener("mouseenter", () => {
        dot.style.opacity  = "1";
        ring.style.opacity = "0.6";
        inner.style.opacity = "0.4";
    });
})();

// ================================================================
// Auto-dismiss de flash messages após 4 segundos
// ================================================================
document.addEventListener("DOMContentLoaded", () => {
    const alertas = document.querySelectorAll(".alert.alert-success, .alert.alert-info");
    alertas.forEach((alerta) => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alerta);
            if (bsAlert) bsAlert.close();
        }, 4000);
    });
});

// ================================================================
// HTMX: após inserir nova linha no dashboard (quick-add),
// remove o aviso "nenhuma transação" se existir
// ================================================================
document.addEventListener("htmx:afterSwap", () => {
    const aviso = document.getElementById("aviso-sem-transacoes");
    if (aviso) aviso.remove();
});

// ================================================================
// Foco automático no campo de valor do quick-add (desktop only)
// ================================================================
document.addEventListener("DOMContentLoaded", () => {
    const campoValorRapido = document.getElementById("valor-rapido");
    if (campoValorRapido && window.innerWidth >= 768) {
        campoValorRapido.focus();
    }
});
