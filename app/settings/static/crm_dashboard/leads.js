(function () {
  var draggedCard = null;
  var dragOrigin = null;
  var dropCommitted = false;

  function ready(fn) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", fn);
    } else {
      fn();
    }
  }

  ready(function () {
    var toggle = document.querySelector("[data-lead-filter-toggle]");
    var filters = document.querySelector("[data-lead-filters]");
    var board = document.querySelector(".crm-lead-board");
    var modal = document.querySelector("[data-lead-modal]");
    var exportAll = document.querySelector("[data-lead-export-all]");

    if (toggle && filters) {
      toggle.addEventListener("click", function () {
        filters.classList.toggle("is-hidden");
      });
    }

    document.querySelectorAll("[data-lead-dd]").forEach(function (dropdown) {
      var menuToggle = dropdown.querySelector("[data-lead-menu-toggle]");
      if (!menuToggle) return;
      menuToggle.addEventListener("click", function (event) {
        event.stopPropagation();
        document.querySelectorAll("[data-lead-dd].is-open").forEach(function (openDropdown) {
          if (openDropdown !== dropdown) openDropdown.classList.remove("is-open");
        });
        dropdown.classList.toggle("is-open");
      });
    });

    document.addEventListener("click", function (event) {
      document.querySelectorAll("[data-lead-dd].is-open").forEach(function (dropdown) {
        if (!dropdown.contains(event.target)) dropdown.classList.remove("is-open");
      });
    });

    document.querySelectorAll("[data-lead-modal-open]").forEach(function (button) {
      button.addEventListener("click", function () {
        document.querySelectorAll("[data-lead-dd].is-open").forEach(function (dropdown) {
          dropdown.classList.remove("is-open");
        });
        if (modal) modal.classList.remove("is-hidden");
        document.body.classList.add("crm-drawer-open");
      });
    });

    document.querySelectorAll("[data-lead-modal-close]").forEach(function (button) {
      button.addEventListener("click", closeLeadModal);
    });

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") closeLeadModal();
    });

    if (exportAll) {
      exportAll.addEventListener("change", function () {
        document.querySelectorAll('input[name="fields"]').forEach(function (checkbox) {
          checkbox.checked = exportAll.checked;
        });
      });
    }

    if (board) {
      board.addEventListener(
        "wheel",
        function (event) {
          if (Math.abs(event.deltaY) <= Math.abs(event.deltaX)) return;
          if (board.scrollWidth <= board.clientWidth) return;
          board.scrollLeft += event.deltaY;
          event.preventDefault();
        },
        { passive: false }
      );

      board.addEventListener("dragstart", function (event) {
        var card = event.target.closest("[data-lead-card]");
        if (!card) return;
        draggedCard = card;
        dropCommitted = false;
        dragOrigin = {
          parent: card.parentNode,
          next: card.nextElementSibling,
          status: card.getAttribute("data-lead-status"),
        };
        event.dataTransfer.effectAllowed = "move";
        event.dataTransfer.setData("text/plain", card.getAttribute("data-lead-id") || "");
        window.setTimeout(function () {
          card.classList.add("is-dragging");
        }, 0);
      });

      board.addEventListener("dragend", function () {
        if (draggedCard) {
          draggedCard.classList.remove("is-dragging");
        }
        document.querySelectorAll("[data-lead-column].is-over").forEach(function (column) {
          column.classList.remove("is-over");
        });
        if (!dropCommitted && draggedCard) {
          restoreCard(draggedCard);
          clearDragState();
        }
        refreshBoard();
      });

      board.addEventListener("dragover", function (event) {
        var column = event.target.closest("[data-lead-column]");
        if (!column || !draggedCard) return;
        event.preventDefault();
        event.dataTransfer.dropEffect = "move";
        column.classList.add("is-over");

        var dropzone = column.querySelector("[data-lead-dropzone]");
        var before = getCardAfter(dropzone, event.clientY);
        if (before) {
          dropzone.insertBefore(draggedCard, before);
        } else {
          dropzone.appendChild(draggedCard);
        }
        refreshBoard();
      });

      board.addEventListener("dragleave", function (event) {
        var column = event.target.closest("[data-lead-column]");
        if (!column || column.contains(event.relatedTarget)) return;
        column.classList.remove("is-over");
      });

      board.addEventListener("drop", function (event) {
        var column = event.target.closest("[data-lead-column]");
        if (!column || !draggedCard) return;
        event.preventDefault();
        dropCommitted = true;
        column.classList.remove("is-over");
        saveCardStatus(draggedCard, column.getAttribute("data-target-status"));
      });

      refreshBoard();
    }

    function closeLeadModal() {
      if (!modal || modal.classList.contains("is-hidden")) return;
      modal.classList.add("is-hidden");
      document.body.classList.remove("crm-drawer-open");
    }
  });

  function getCookie(name) {
    var value = "; " + document.cookie;
    var parts = value.split("; " + name + "=");
    if (parts.length === 2) return parts.pop().split(";").shift();
    return "";
  }

  function getCsrfToken() {
    var meta = document.querySelector('meta[name="csrf-token"]');
    return (meta && meta.getAttribute("content")) || getCookie("csrftoken");
  }

  function getCardAfter(dropzone, y) {
    var cards = Array.prototype.slice.call(
      dropzone.querySelectorAll("[data-lead-card]:not(.is-dragging)")
    );
    return cards.reduce(
      function (closest, child) {
        var box = child.getBoundingClientRect();
        var offset = y - box.top - box.height / 2;
        if (offset < 0 && offset > closest.offset) {
          return { offset: offset, element: child };
        }
        return closest;
      },
      { offset: Number.NEGATIVE_INFINITY, element: null }
    ).element;
  }

  function refreshBoard() {
    document.querySelectorAll("[data-lead-column]").forEach(function (column) {
      var count = column.querySelectorAll("[data-lead-card]").length;
      var countNode = column.querySelector("[data-lead-count]");
      var emptyNode = column.querySelector("[data-lead-empty]");
      if (countNode) countNode.textContent = count;
      if (emptyNode) emptyNode.classList.toggle("is-hidden", count > 0);
    });
  }

  function restoreCard(card) {
    if (!dragOrigin || !dragOrigin.parent) return;
    if (dragOrigin.next && dragOrigin.next.parentNode === dragOrigin.parent) {
      dragOrigin.parent.insertBefore(card, dragOrigin.next);
    } else {
      dragOrigin.parent.appendChild(card);
    }
    card.setAttribute("data-lead-status", dragOrigin.status || "");
    refreshBoard();
  }

  function clearDragState() {
    draggedCard = null;
    dragOrigin = null;
    dropCommitted = false;
  }

  function updateCardTone(card, data) {
    var badge = card.querySelector(".crm-lead-badge");
    card.classList.remove("crm-lead-card--warning", "crm-lead-card--success", "crm-lead-card--muted");
    card.classList.add("crm-lead-card--" + (data.tone || "warning"));
    if (badge && data.badge) badge.textContent = data.badge;
  }

  function saveCardStatus(card, status) {
    if (!status || status === card.getAttribute("data-lead-status")) {
      refreshBoard();
      clearDragState();
      return;
    }

    var url = card.getAttribute("data-status-url");
    var body = new URLSearchParams();
    body.set("status", status);
    card.classList.add("is-saving");

    fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-CSRFToken": getCsrfToken(),
        "X-Requested-With": "XMLHttpRequest",
      },
      body: body.toString(),
      credentials: "same-origin",
    })
      .then(function (response) {
        if (!response.ok) throw new Error("status update failed");
        return response.json();
      })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || "status update failed");
        card.setAttribute("data-lead-status", data.status || status);
        updateCardTone(card, data);
        refreshBoard();
      })
      .catch(function () {
        restoreCard(card);
      })
      .finally(function () {
        card.classList.remove("is-saving");
        clearDragState();
      });
  }
})();
