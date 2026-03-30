const openModalButtons = document.querySelectorAll("[data-open-modal]");
const closeModalButtons = document.querySelectorAll("[data-close-modal]");

const closeInlineEditors = () => {
  document.querySelectorAll(".post.is-editing").forEach((post) => {
    post.classList.remove("is-editing");
    const editBlock = post.querySelector(".post-edit-inline");
    if (editBlock) {
      editBlock.classList.add("hidden");
    }
  });
};

const closeModal = (modal) => {
  if (!modal) return;
  modal.style.display = "none";
  modal.setAttribute("aria-hidden", "true");
};

const openModal = (modal) => {
  if (!modal) return;
  modal.style.display = "flex";
  modal.setAttribute("aria-hidden", "false");
};

openModalButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const targetModalId = button.dataset.openModal || "modal";
    const targetModal = document.getElementById(targetModalId);
    openModal(targetModal);
  });
});

closeModalButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const parentModal = button.closest(".modal");
    closeModal(parentModal);
  });
});

document.querySelectorAll(".modal").forEach((modal) => {
  modal.addEventListener("click", (event) => {
    if (event.target === modal) {
      closeModal(modal);
    }
  });
});

document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape") return;
  closeInlineEditors();
  document.querySelectorAll('.modal[aria-hidden="false"]').forEach((modal) => {
    closeModal(modal);
  });
});

document.addEventListener("click", (event) => {
  const openInlineEditButton = event.target.closest("[data-inline-edit]");
  if (openInlineEditButton) {
    const post = openInlineEditButton.closest(".post");
    const targetInlineEditId = openInlineEditButton.dataset.inlineEdit;
    const editBlock = targetInlineEditId
      ? document.getElementById(targetInlineEditId)
      : null;

    if (!post || !editBlock) return;

    closeInlineEditors();
    post.classList.add("is-editing");
    editBlock.classList.remove("hidden");

    const textarea = editBlock.querySelector("textarea");
    if (textarea) {
      textarea.focus();
      const contentLength = textarea.value.length;
      textarea.setSelectionRange(contentLength, contentLength);
    }
    return;
  }

  const cancelInlineEditButton = event.target.closest("[data-cancel-inline-edit]");
  if (cancelInlineEditButton) {
    const post = cancelInlineEditButton.closest(".post");
    if (!post) return;

    post.classList.remove("is-editing");
    const editBlock = post.querySelector(".post-edit-inline");
    if (editBlock) {
      editBlock.classList.add("hidden");
    }
    return;
  }

  const commentsButton = event.target.closest(".comments-btn");
  if (!commentsButton) return;

  const post = commentsButton.closest(".post");
  if (!post) return;

  const comments = post.querySelector(".comments");
  if (!comments) return;

  comments.classList.toggle("hidden");
});
