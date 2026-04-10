(function () {
  try {
    var s = localStorage.getItem("fontScale");
    if (s && s !== "100") {
      document.documentElement.setAttribute("data-font-scale", s);
    }
  } catch (e) {}
})();
