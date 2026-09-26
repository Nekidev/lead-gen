function resize(target) {
  target.style.height = 0;
  target.style.height = `${target.scrollHeight}px`;
}

function count(string, substring) {
  return (string.match(substring) || []).length;
}

window.addEventListener("load", () => {
  for (const input of document.getElementsByTagName("textarea")) {
    resize(input);
    input.addEventListener("input", (event) => resize(event.currentTarget));
  }
});
