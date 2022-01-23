export default function renderTicker(id, data) {
    const { lang } = document.documentElement;
    const ticker = document.getElementById(id);
    const { clientWidth } = ticker;
    let position = localStorage.getItem(id) || Math.round(clientWidth * 0.6);

    data.forEach((news) => {
        let el = document.createElement("a");

        el.href = news.url;
        el.classList = "ticker__link";
        el.dataset.toggle = "tooltip";
        el.dataset.title =
            lang === "ru"
                ? "Открыть ссылку в новой вкладке"
                : "Оpen link in new tab";
        el.innerText = news.title;
        el.target = "_blank";
        ticker.appendChild(el);
    });

    const initTicker = () => {
        const { scrollWidth } = ticker;
        let step = 1;
        let isHovered = false;

        function launchTicker() {
            if (isHovered) {
                return;
            }

            position -= step;
            ticker.style.transform = `translateX(${position}px)`;

            if (Math.abs(position) > scrollWidth) {
                position = clientWidth;
            }

            localStorage.setItem(id, position);

            requestAnimationFrame(launchTicker);
        }

        ticker.addEventListener("mouseleave", () => {
            isHovered = false;
            requestAnimationFrame(launchTicker);
        });

        ticker.addEventListener("mouseenter", () => (isHovered = true));

        requestAnimationFrame(launchTicker);
    };

    initTicker();
    localStorage.setItem(id, position);
}
