/**
 * dash-reportbuilder: SortableJS auto-initialization.
 *
 * Watches for elements with class "drb-sortable-list" and initializes
 * SortableJS for drag-and-drop reordering.  The DOM order is read by
 * a Dash clientside callback at export time — no JS→Python bridge
 * needed during dragging.
 */
(function() {
    "use strict";

    function initSortable(el) {
        if (typeof Sortable === "undefined") return;
        if (el._drbSortable) {
            el._drbSortable.destroy();
            el._drbSortable = null;
        }
        el._drbSortable = new Sortable(el, {
            handle: ".drb-drag-handle",
            animation: 150,
            ghostClass: "drb-sortable-ghost"
        });
    }

    function initAll() {
        document.querySelectorAll(".drb-sortable-list").forEach(initSortable);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initAll);
    } else {
        initAll();
    }

    // Re-init after Dash re-renders
    new MutationObserver(function(mutations) {
        for (var i = 0; i < mutations.length; i++) {
            if (mutations[i].type === "childList") {
                clearTimeout(window._drbTimer);
                window._drbTimer = setTimeout(initAll, 100);
                return;
            }
        }
    }).observe(document.body || document.documentElement, {
        childList: true, subtree: true
    });
})();
