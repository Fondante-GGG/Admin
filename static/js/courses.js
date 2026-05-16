// document.addEventListener('DOMContentLoaded', function () {
//     const buttons = document.querySelectorAll('.data_btns button');
//     const contents = document.querySelectorAll('.data_info_content');

//     buttons.forEach(button => {
//         button.addEventListener('click', () => {
//             buttons.forEach(btn => btn.classList.remove('active'));

//             button.classList.add('active');

//             contents.forEach(content => {
//                 content.style.display = 'none';
//             });

//             const categoryId = button.getAttribute('data-category');
//             const targetContent = document.getElementById(categoryId);
//             targetContent.style.display = 'flex';
//         });
//     });
// });

// const modalButtons = document.querySelectorAll('.detailed');
// const modal = document.querySelector('.modal');
// const modalClose = document.querySelector('button');

// let scrollPosition;

// modalButtons.forEach(btn => {
//     btn.addEventListener('click', () => {
//         scrollPosition = window.scrollY;
//         document.body.style.top = `-${scrollPosition}px`;
//         document.body.style.position = 'fixed';
//         document.body.style.width = '100%';
//         modal.classList.add('active');
//     });
// });

// function closeModal() {
//     const content = modal.querySelector('.modal_content');
//     content.style.transform = 'translateY(100%)';
//     content.style.display = "none"

//     setTimeout(() => {
//         modal.classList.remove('active');
//         document.body.style.position = '';
//         document.body.style.top = '';
//         document.body.style.width = '100%';
//         // window.scrollTo(0, scrollPosition);
//         content.style.transform = '';
//     }, 300);
// }

// modalClose.addEventListener('click', closeModal);

// modal.addEventListener('click', (e) => {
//     if (e.target === modal) {
//         closeModal();
//     }
// });

// const signupButtons = document.querySelectorAll('.signup');
// const modalSign = document.querySelector('.modalSign');
// const modalSignClose = document.querySelector('.modalSign_close');

// signupButtons.forEach(button => {
//     button.addEventListener('click', () => {
//         scrollPosition = window.scrollY;
//         document.body.style.top = `-${scrollPosition}px`;
//         document.body.style.position = 'fixed';
//         document.body.style.width = '100%';
//         modalSign.style.display = 'block';
//     });
// });

// modalSignClose.addEventListener('click', () => {
//     modalSign.style.display = 'none';
//     document.body.style.position = '';
//     document.body.style.top = '';
//     document.body.style.width = '';
//     window.scrollTo(0, scrollPosition);
// });

// window.addEventListener('click', (e) => {
//     if (e.target === modalSign) {
//         modalSign.style.display = 'none';
//         document.body.style.position = '';
//         document.body.style.top = '';
//         document.body.style.width = '';
//         window.scrollTo(0, scrollPosition);
//     }
// });
