const swiper = new Swiper('.courses-slider', {
    slidesPerView: 2.5,
    spaceBetween: 20,
    mousewheel: false, // Отключение прокрутки мышью
    keyboard: {
        enabled: true, // Включение управления клавиатурой
        onlyInViewport: true,
    },
    loop: true, // Бесконечный цикл
    autoplay: {
        delay: 5000, // Автопрокрутка каждые 5 секунд
        disableOnInteraction: false, // Не отключать при взаимодействии
    },
    navigation: {
        nextEl: '.swiper-button-next',
        prevEl: '.swiper-button-prev',
    },
    breakpoints: {
        320: {
            slidesPerView: 1, // Отображать 1 слайд на маленьких экранах
            spaceBetween: 10
        },
        576: {
            slidesPerView: 1.5, // Отображать 1.5 слайда на средних экранах
            spaceBetween: 15
        },
        768: {
            slidesPerView: 2, // Отображать 2 слайда на планшетах
            spaceBetween: 20
        },
        1200: {
            slidesPerView: 2.5, // Отображать 2.5 слайда на больших экранах
            spaceBetween: 20
        }
    }
});

export default swiper;
