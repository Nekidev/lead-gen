import hljs from "https://esm.sh/highlight.js/lib/core";
import django from "https://esm.sh/highlight.js/lib/languages/django";

hljs.registerLanguage("django", django);

const highlightedInputs = document.querySelectorAll(".highlighted-input");

for (const container of highlightedInputs) {
  const input = container.querySelector("input, textarea");
  const pre = container.getElementsByTagName("pre")[0];

  function handleInput() {
    const code = input.value;
    const codeHighlighted = hljs.highlight(code, {
      language: "django",
    }).value;
    pre.innerHTML = codeHighlighted;
  }
  function handleScroll() {
    pre.scrollTop = input.scrollTop;
    pre.scrollLeft = input.scrollLeft;
  }

  input.addEventListener("input", handleInput);
  input.addEventListener("change", handleInput);
  input.addEventListener("scroll", handleScroll);

  handleInput();
  handleScroll();
}
