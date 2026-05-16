const teacherMenuItems = document.querySelectorAll('.teachers_menu > div');
const teacherInfos = document.querySelectorAll('.teacher_info_block');

// Активируем первый элемент по умолчанию
teacherMenuItems[0].classList.add('active');
teacherInfos[0].classList.add('active');

teacherMenuItems.forEach((item, index) => {
    item.addEventListener('click', () => {
        // Убираем активный класс у всех элементов
        teacherMenuItems.forEach(i => i.classList.remove('active'));
        teacherInfos.forEach(i => i.classList.remove('active'));

        // Добавляем активный класс выбранным элементам
        item.classList.add('active');
        teacherInfos[index].classList.add('active');
    });
});
