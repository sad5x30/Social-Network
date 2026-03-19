const openModalButtons = document.querySelectorAll("[data-open-modal]");
const closeModalButtons = document.querySelectorAll("[data-close-modal]");

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
  document.querySelectorAll('.modal[aria-hidden="false"]').forEach((modal) => {
    closeModal(modal);
  });
});

document.addEventListener("click", (event) => {
  const commentsButton = event.target.closest(".comments-btn");
  if (!commentsButton) return;

  const post = commentsButton.closest(".post");
  if (!post) return;

  const comments = post.querySelector(".comments");
  if (!comments) return;

  comments.classList.toggle("hidden");
});
