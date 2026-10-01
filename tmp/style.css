const logosWrap = document.querySelectorAll(".logos-wrap");
const line3 = document.querySelector("#line-3");
const rule = document.querySelector(".rule");
const rules = rule.querySelectorAll("div");
let targets = [];

logosWrap.forEach((item) => {
  targets.push(item.querySelectorAll("img"));
  return targets;
});

const options = {
  root: document.querySelector(".logos"),
  rootMargin: "0px",
  threshold: 1
};

const observerImg = () => {
  const callback = (e) => {
    e.forEach((i) => {
      if (i.intersectionRatio <= 0) {
        i.target.classList.remove("logoShow");
      }
      if (i.isIntersecting) {
        i.target.classList.add("logoShow");
      }
    });
  };

  const observer = new IntersectionObserver(callback, options);

  targets.forEach((item) => {
    item.forEach((i) => {
      observer.observe(i);
    });
  });
};

window.onload = observerImg;
